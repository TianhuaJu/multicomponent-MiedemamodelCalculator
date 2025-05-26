
"""symbolic_binary.py

本文件基于用户上传的 05b5f7a1-fa17-485a-8497-5af2a5c3d63b.py，将所有主要热力学/热物性计算函数改写为 **符号化**（SymPy）形式，便于解析、推导、自动求导及后续与 CALPHAD‑style 表达式耦合。

说明
----
* 依赖 `sympy >= 1.12`。
* 数值常量仍来源于数据库，但被包装为 `sp.Float`，  可在符号表达式中与变量同等处理。
* 体积自洽方程 `_V_in_alloy` 原代码迭代求解。  这里改写为返回两个 **方程对象** `Eq(V1, expression)` 与 `Eq(V2, expression)`，  用户可用 `sp.nsolve` / `sp.solve` 自行求解。
* 所有宏观热力学量（ΔH_mix, ΔS_ex, ΔG_ex, lnγ_i）  现在返回 **SymPy 符号表达式**，变量集合：  
  `xA, xB, T` （且满足 `xA + xB = 1`）。

作者：自动生成（{date})
"""

import os
import sqlite3 as sq
import sympy as sp
from sympy import symbols, Eq, Float

__all__ = [  # 导出主要类
    'Element',
    'BinarySymbolic'
]


# ---------------------------------------------------------------------------
# 数据层：保持与原版一致，但把数字转成 sympy.Float 以便参与符号运算
# ---------------------------------------------------------------------------

class Element:
    """存储元素物性参数；数值包装为 ``sympy.Float``"""

    def __init__(self, symbol: str, table: str = 'Miedema1983'):
        self.symbol = symbol
        self._query(symbol, table)

    # --- DB 查询核心 -------------------------------------------------------

    def _query(self, symbol: str, table: str):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'BinaryData', 'Miedema_physical_parmeter.db')

        cmd = ("SELECT phi, nws, V, u, alpha_beta, hybirdvalue, isTrans, "
               "dHtrans, mass, Tm, Tb, name FROM {} WHERE Symbol=?".format(table))

        with sq.connect(db_path) as conn:
            row = conn.execute(cmd, (symbol,)).fetchone()

        if row is None:
            raise ValueError(f'元素 {symbol} 不存在于数据表 {table}')

        # 数值字段 → sympy.Float
        (phi, nws, V, u, alpha_beta, hyb, isTrans,
         dHtrans, mass, Tm, Tb, name) = row

        self.phi, self.nws, self.V, self.u   = map(Float, (phi, nws, V, u))
        self.alpha_beta = alpha_beta
        self.hybirdvalue = Float(hyb)
        self.isTrans = bool(isTrans)
        self.dHtrans = Float(dHtrans)
        self.mass, self.Tm, self.Tb = map(Float, (mass, Tm, Tb))
        self.name = name

    # --- 方便调试 ---------------------------------------------------------

    def __repr__(self):
        return f"<Element {self.symbol}: φ={self.phi}, n_ws={self.nws}>"


# ---------------------------------------------------------------------------
# 二元体系：符号化版
# ---------------------------------------------------------------------------

class BinarySymbolic:
    """二元合金体系（符号化表达）

    变量
    ----
    xA, xB : `sympy.Symbol`
        摩尔分数；默认满足 ``xA + xB = 1``。
    T      : `sympy.Symbol`
        温度（K）。
    """

    # ---- 初始化 -----
    def __init__(self, A: str, B: str, phase_state: str, order_degree: str = 'IM'):
        self.A = Element(A)
        self.B = Element(B)

        # 相‑态因子 α
        if phase_state == 'S':
            self.alpha = Float(1.0)
        elif phase_state == 'L':
            self.alpha = Float(0.73)
        else:
            raise ValueError('phase_state 只能取 "S" 或 "L"')

        # 有序度 λ
        order_map = {'SS': 0.0, 'AMP': 5.0, 'IM': 8.0}
        if order_degree not in order_map:
            raise ValueError('order_degree 必须是 SS/AMP/IM')
        self.lam = Float(order_map[order_degree])

        # 定义符号变量
        self.xA, self.xB, self.T = symbols('xA xB T', positive=True)
        # 约束 xA+xB=1，可在后续 substitute 或 solve
        self.constraints = [Eq(self.xA + self.xB, 1)]

    # ---------------------------------------------------------------------
    # (1) 体积自洽方程（返回方程而非数值）
    # ---------------------------------------------------------------------
    def volume_equations(self):
        """返回描述 V_A(a), V_B(a) 自洽关系的两条方程 (Eq)"""
        V1, V2 = symbols('V_Aa V_Ba', positive=True)

        A, B = self.A, self.B
        x1, x2 = self.xA, self.xB
        lam = self.lam

        # 中间量
        Pax = x1 * V1 / (x2 * V2 + x1 * V1)
        Pbx = x2 * V2 / (x2 * V2 + x1 * V1)

        eq1 = Eq(V1,
                 A.V * (1 + A.u * Pbx * (1 + lam * (Pax * Pbx)**2) * (A.phi - B.phi)))
        eq2 = Eq(V2,
                 B.V * (1 + B.u * Pax * (1 + lam * (Pax * Pbx)**2) * (B.phi - A.phi)))
        return eq1, eq2, {V1, V2}

    # ---------------------------------------------------------------------
    # (2) Miedema 生成热 (ΔH_mix) —— 符号表达式
    # ---------------------------------------------------------------------
    def H_miedema(self):
        x1, x2 = self.xA, self.xB
        A, B = self.A, self.B
        lam, alpha = self.lam, self.alpha

        # 杂化贡献
        r2p = sp.Integer(0)
        if (A.alpha_beta != 'other') and (B.alpha_beta != 'other') and (A.alpha_beta != B.alpha_beta):
            r2p = alpha * A.hybirdvalue * B.hybirdvalue

        # p_AB
        p_AB = Float(14.2) if (A.isTrans and B.isTrans)                else Float(12.35) if (A.isTrans or B.isTrans)                else Float(10.7)

        df = 2 * p_AB * (
            -(A.phi - B.phi)**2
            + Float(9.4) * (A.nws - B.nws)**2
            - r2p
        ) / (1/A.nws + 1/B.nws)

        # 体积需先解；这里保留符号 Va, Vb
        eq1, eq2, vols = self.volume_equations()
        Va, Vb = list(vols)

        cAs = x1 * Va / (x1 * Va + x2 * Vb)
        cBs = x2 * Vb / (x1 * Va + x2 * Vb)
        fC = cAs * cBs * (1 + lam * (cAs * cBs)**2) * (x1 * Va + x2 * Vb)

        dH_trans = x1 * A.dHtrans + x2 * B.dHtrans
        return fC * df + dH_trans  # kJ/mol

    # ---------------------------------------------------------------------
    # (3) Tanaka 过量熵 ΔS_ex —— 符号表达式
    # ---------------------------------------------------------------------
    def S_excess(self):
        A, B = self.A, self.B
        Hmix = self.H_miedema()
        TmA, TmB = A.Tm, B.Tm
        alpha = self.alpha

        if alpha == Float(0.73):
            factor = Float(1)/Float(14) * (1/TmA + 1/TmB)
        else:
            factor = Float(1)/Float(15.1) * (1/TmA + 1/TmB)
        return factor * Hmix  # kJ/K·mol

    # ---------------------------------------------------------------------
    # (4) 过量 Gibbs 自由能 ΔG_ex
    # ---------------------------------------------------------------------
    def G_excess(self):
        return self.H_miedema() - self.T * self.S_excess()

    # ---------------------------------------------------------------------
    # (5) 稀释极限下的对数活度 lnγ (A,B)
    # ---------------------------------------------------------------------
    def ln_gamma_A_infinite_dilute(self):
        # 对应原 d_fun10
        A, B = self.A, self.B
        T = self.T
        alpha = self.alpha

        special = ('Si', 'Ge', 'C', 'P')
        dH_trans = sp.Integer(0)
        if alpha == Float(0.73):
            if A.symbol in special:
                dH_trans = B.dHtrans
            entropy_factor = Float(1)/Float(14) * (1/A.Tm + 1/B.Tm)
        else:
            dH_trans = B.dHtrans
            entropy_factor = Float(1)/Float(15.2) * (1/A.Tm + 1/B.Tm)

        # 杂化
        r2p = sp.Integer(0)
        if (A.alpha_beta != 'other') and (B.alpha_beta != 'other') and (A.alpha_beta != B.alpha_beta):
            r2p = alpha * A.hybirdvalue * B.hybirdvalue

        p_AB = Float(14.2) if (A.isTrans and B.isTrans)                else Float(12.35) if (A.isTrans or B.isTrans)                else Float(10.7)

        df = 2 * p_AB * (-(A.phi - B.phi)**2 + Float(9.4)*(A.nws - B.nws)**2 - r2p)              / (1/A.nws + 1/B.nws)

        lnY0 = 1000*df*B.V*(1 + B.u*(B.phi - A.phi))/(Float(8.314)*T)                + 1000*dH_trans/(Float(8.314)*T)
        return lnY0 * (1 - entropy_factor)

    def ln_gamma_B_infinite_dilute(self):
        # 直接交换 A,B 调用上式即可
        origA, origB = self.A, self.B
        # 临时交换并调用
        self.A, self.B = origB, origA
        res = self.ln_gamma_A_infinite_dilute()
        # 复原
        self.A, self.B = origA, origB
        return res
