
"""multicomponent_symbolic.py

符号化多元合金热力学骨架 + 与 pycalphad 集成示例
------------------------------------------------
* 支持 N 组元 (N≥2) 的 Miedema 生成热、Tanaka 过量熵、ΔG^ex。
* 提供 ``solve_volumes_numerical`` 自动求解自洽体积。
* 提供 ``build_pycalphad_expression`` 生成 SymEngine 表达式，可注入
  ``pycalphad.Model`` 的 ``self.GM`` 或作为自定义模型扩展。

依赖
----
sympy  >= 1.12
pycalphad >= 0.10  (# 仅在集成示例中需要)

作者  : ChatGPT auto‑gen
日期  : 2025-05-04
"""

from __future__ import annotations
import os, sqlite3 as sq, itertools
from typing import List, Dict, Tuple
import sympy as sp
from sympy import Symbol, Float, Eq
try:
    import pycalphad.variables as v
    from sympy_converter import sympy_to_symbol
    HAS_PYCALPHAD = True
except ImportError:
    HAS_PYCALPHAD = False


# ----------------------------------------------------------
# 基础：元素数据（与二元版相同，只保留必要字段）
# ----------------------------------------------------------

class Element:
    _db_path = os.path.join(os.path.dirname(__file__),
                            'BinaryData', 'Miedema_physical_parmeter.db')

    def __init__(self, symbol: str, table: str='Miedema1983'):
        self.symbol = symbol.upper()
        self._load(symbol, table)

    def _load(self, sym: str, table: str):
        cmd = ("SELECT phi, nws, V, u, alpha_beta, hybirdvalue, isTrans, "
               "dHtrans, Tm FROM {} WHERE Symbol=?".format(table))
        with sq.connect(self._db_path) as conn:
            row = conn.execute(cmd, (sym,)).fetchone()
        if row is None:
            raise ValueError(f'元素 {sym} 不在表 {table}')

        (phi, nws, V, u, alpha_beta, hyb, isT, dHt, Tm) = row
        self.phi      = Float(phi)
        self.n_ws     = Float(nws)
        self.V_atom   = Float(V)
        self.u        = Float(u)
        self.alpha_beta   = alpha_beta
        self.hybrid_val   = Float(hyb)
        self.isTrans  = bool(isT)
        self.dH_trans = Float(dHt)
        self.Tm       = Float(Tm)

    def __repr__(self):
        return f"<{self.symbol} φ={self.phi} n_ws={self.n_ws}>"

# ----------------------------------------------------------
# 多元符号体系
# ----------------------------------------------------------

class MulticomponentSymbolic:
    """N 组元符号化模型（Miedema + Tanaka）"""

    def __init__(self, comps: List[str], phase_state='S', order_degree='IM'):
        if len(comps) < 2:
            raise ValueError('至少需要 2 个组元')
        self.elements: Dict[str, Element] = {sym: Element(sym) for sym in comps}
        self.N = len(comps)

        # 符号变量  x_Al, x_Cu ...
        self.x: Dict[str, Symbol] = {sym: sp.symbols(f'x_{sym}') for sym in comps}

        self.T = sp.symbols('T', positive=True)

        # 约束 Σx_i = 1
        self.mass_balance = Eq(sum(self.x.values()), 1)

        # 相态、序度参数
        self.alpha = Float(1.0) if phase_state=='S' else Float(0.73)
        self.lam_map = {'SS':0, 'AMP':5, 'IM':8}
        if order_degree not in self.lam_map:
            raise ValueError('order_degree 必须为 SS/AMP/IM')
        self.lam   = Float(self.lam_map[order_degree])

        # 体积符号 V_Aa ...
        self.vol_syms: Dict[str, Symbol] = {sym: sp.symbols(f'V_{sym}a', positive=True)
                                             for sym in comps}

    # ------------------ 体积方程 -----------------------
    def volume_equations(self) -> List[Eq]:
        eqs = []
        denom = sum(self.x[s]*self.vol_syms[s] for s in self.elements)
        for i, ei in self.elements.items():
            Pi = self.x[i]*self.vol_syms[i]/denom
            term_sum = sum(
                self.x[j]*self.vol_syms[j]/denom *
                (1 + self.lam*(Pi* self.x[j]*self.vol_syms[j]/denom)**2) *
                (ei.phi - self.elements[j].phi)
                for j in self.elements if j!=i
            )
            eqs.append(Eq(self.vol_syms[i],
                          ei.V_atom * (1 + ei.u * term_sum)))
        return eqs

    # ------------------ ΔH_mix -----------------------
    def delta_H_miedema(self):
        terms = []
        denom = sum(self.x[s]*self.vol_syms[s] for s in self.elements)
        for i, j in itertools.combinations(self.elements, 2):
            ei, ej = self.elements[i], self.elements[j]
            p_ij = Float(14.2) if (ei.isTrans and ej.isTrans)                    else Float(12.35) if (ei.isTrans or ej.isTrans)                    else Float(10.7)
            r2p = Float(0)
            if (ei.alpha_beta!='other' and ej.alpha_beta!='other' and
                ei.alpha_beta!=ej.alpha_beta):
                r2p = self.alpha * ei.hybrid_val * ej.hybrid_val
            df = 2*p_ij*(-(ei.phi-ej.phi)**2 + Float(9.4)*(ei.n_ws-ej.n_ws)**2 - r2p) / (1/ei.n_ws+1/ej.n_ws)

            Vi, Vj = self.vol_syms[i], self.vol_syms[j]
            cIs = self.x[i]*Vi/denom
            cJs = self.x[j]*Vj/denom
            fC = cIs*cJs*(1+self.lam*(cIs*cJs)**2)*denom
            terms.append(fC*df)
        dH_trans = sum(self.x[s]*e.dH_trans for s,e in self.elements.items())
        return sum(terms) + dH_trans

    # ------------------ ΔS_ex -----------------------
    def delta_S_excess(self):
        inv_Tm = sum(self.x[s]/self.elements[s].Tm for s in self.elements)
        factor = Float(1)/Float(14) if self.alpha==Float(0.73) else Float(1)/Float(15.1)
        return factor*self.delta_H_miedema()*inv_Tm

    def delta_G_excess(self):
        return self.delta_H_miedema() - self.T*self.delta_S_excess()

    # ------------------ 数值求解 -----------------------
    def solve_volumes_numerical(self, x_dict: Dict[str,float], T: float,
                                guesses: Dict[str,float]|None=None):
        subs = { self.x[s]: x_dict[s] for s in self.elements}
        subs[self.T] = T
        eqs = [eq.subs(subs) for eq in self.volume_equations()]
        vars_ = list(self.vol_syms.values())
        if guesses is None:
            guesses = {s: float(e.V_atom) for s,e in self.elements.items()}
        init = [guesses[s] for s in self.elements]
        sol = sp.nsolve(eqs, vars_, init)
        return {str(v): float(val) for v,val in zip(vars_, sol)}

    # ------------------ 转为 pycalphad 表达式 -----------------------
    def build_pycalphad_expression(self, comp_to_sitevar: Dict[str, 'v.SiteFraction']):
        if not HAS_PYCALPHAD:
            raise RuntimeError('pycalphad 未安装')
        expr_sympy = sp.simplify(self.delta_G_excess())
        repl = { self.x[s]: comp_to_sitevar[s] for s in self.elements}
        sympy_expr = expr_sympy.subs(repl)
        return sympy_to_symbol(sympy_expr)

