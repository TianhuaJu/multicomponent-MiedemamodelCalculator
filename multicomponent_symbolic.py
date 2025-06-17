import sympy as sp
from sympy import symbols, exp, log, sqrt, Abs, Piecewise, simplify, integrate
from typing import Union, Callable, Dict, List
import math
from symbolic_binary import*

# 符号计算版本的外推模型函数
extrap_func_symbolic = Callable[[str, str, str, Union[float, sp.Symbol], str, str], Union[float, sp.Symbol]]


def Kohler_symbolic (k: str, i: str, j: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> Union[
	float, sp.Symbol]:
	"""符号计算版本的Kohler模型"""
	return 0


def Muggianu_symbolic (k: str, i: str, j: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> \
Union[float, sp.Symbol]:
	"""符号计算版本的Muggianu模型"""
	return sp.Rational(1, 2)


def _asym_component_choice_symbolic (k: str, i: str, j: str, phase_state: str, order_degree: str) -> str:
	"""符号计算版本的Qiao非对称组分选择规则"""
	# 计算二元焓
	try:
		bij = BinarySymbolic(i, j, phase_state=phase_state, order_degree=order_degree)
		bik = BinarySymbolic(i, k, phase_state=phase_state, order_degree=order_degree)
		bjk = BinarySymbolic(j, k, phase_state=phase_state, order_degree=order_degree)
		
		# 使用数值计算来做决策（符号计算对于决策逻辑太复杂）
		a = float(bij.getEnthalpy_byMiedema_Model_symbolic(0.5, 0.5).subs(bij.Tem, 1000))
		b = float(bik.getEnthalpy_byMiedema_Model_symbolic(0.5, 0.5).subs(bik.Tem, 1000))
		c = float(bjk.getEnthalpy_byMiedema_Model_symbolic(0.5, 0.5).subs(bjk.Tem, 1000))
		
		# 应用选择规则
		if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
			a = abs(a)
			b = abs(b)
			c = abs(c)
			
			t = min(a, b)
			t2 = min(t, c)
			if t2 == a:
				return k
			if t2 == b:
				return j
			else:
				return i
		else:
			t = c if a * b > 0 else b if a * c > 0 else a
			if t == a:
				return k
			if t == b:
				return j
			else:
				return i
	except:
		# 如果失败，返回默认选择
		return i


def _beta_kj_symbolic (k: str, j: str, i: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> \
Union[float, sp.Symbol]:
	"""符号计算版本的Chou模型中的偏差函数（beta_k-j）"""
	# 创建二元系统
	bik = BinarySymbolic(i, k, phase_state=phase_state, order_degree=order_degree)
	bij = BinarySymbolic(i, j, phase_state=phase_state, order_degree=order_degree)
	bik.set_T_symbolic(T)
	bij.set_T_symbolic(T)
	
	# 定义积分函数（符号版本）
	x = sp.Symbol('x', real=True)
	
	# 计算过量吉布斯能差
	gibbs_diff = (bik.get_excess_Gibbs_symbolic(x, 1.0 - x) -
	              bij.get_excess_Gibbs_symbolic(x, 1.0 - x))
	
	# 计算积分 ∫[0,1] (ΔG)² dx
	integrand = gibbs_diff ** 2
	
	try:
		# 尝试符号积分
		if isinstance(T, sp.Symbol):
			# 对于符号温度，返回符号表达式
			result = sp.integrate(integrand, (x, 0, 1))
			return result
		else:
			# 对于数值温度，计算数值积分
			integrand_func = sp.lambdify(x, integrand.subs(T, float(T)), 'numpy')
			from scipy.integrate import quad
			result, _ = quad(integrand_func, 0, 1)
			return result
	except:
		# 如果积分失败，使用简化方法
		# 在x=0.5处评估函数作为近似
		approx_value = gibbs_diff.subs(x, 0.5) ** 2
		return approx_value


def _df_UEM1_symbolic (k: str, i: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> Union[
	float, sp.Symbol]:
	"""符号计算版本的UEM1模型属性差计算"""
	bik = BinarySymbolic(i, k, phase_state=phase_state, order_degree=order_degree)
	bik.set_T_symbolic(T)
	lnYi0 = bik.d_fun10_symbolic()
	lnYk0 = bik.d_fun20_symbolic()
	return sp.Abs(lnYk0 - lnYi0)


def UEM2_N_symbolic (k: str, i: str, j: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> Union[
	float, sp.Symbol]:
	"""符号计算版本的UEM2模型交互属性差计算"""
	# 创建二元系统
	bij = BinarySymbolic(i, j, phase_state=phase_state, order_degree=order_degree)
	bkj = BinarySymbolic(k, j, phase_state=phase_state, order_degree=order_degree)
	bij.set_T_symbolic(T)
	bkj.set_T_symbolic(T)
	bji = BinarySymbolic(j, i, phase_state=phase_state, order_degree=order_degree)
	bki = BinarySymbolic(k, i, phase_state=phase_state, order_degree=order_degree)
	bji.set_T_symbolic(T)
	bki.set_T_symbolic(T)
	
	# 定义积分变量
	x = sp.Symbol('x', real=True)
	
	# 定义过量吉布斯能函数
	wij = bij.get_excess_Gibbs_symbolic(x, 1 - x)
	wkj = bkj.get_excess_Gibbs_symbolic(x, 1 - x)
	wji = bji.get_excess_Gibbs_symbolic(x, 1 - x)
	wki = bki.get_excess_Gibbs_symbolic(x, 1 - x)
	
	try:
		# 计算积分
		if isinstance(T, sp.Symbol):
			Wkj = sp.integrate(wkj, (x, 0, 1))
			Wji = sp.integrate(wji, (x, 0, 1))
			Wki = sp.integrate(wki, (x, 0, 1))
			Wij = sp.integrate(wji, (x, 0, 1))
		else:
			# 数值积分
			from scipy.integrate import quad
			T_val = float(T)
			Wkj = quad(lambda x_val: float(wkj.subs([(x, x_val), (T, T_val)])), 0, 1)[0]
			Wji = quad(lambda x_val: float(wji.subs([(x, x_val), (T, T_val)])), 0, 1)[0]
			Wki = quad(lambda x_val: float(wki.subs([(x, x_val), (T, T_val)])), 0, 1)[0]
			Wij = quad(lambda x_val: float(wji.subs([(x, x_val), (T, T_val)])), 0, 1)[0]
		
		df_kj = sp.Abs((Wki - Wji) / (Wki + Wji))
		df_ki = sp.Abs((Wkj - Wij) / (Wkj + Wij))
		
		result = df_kj / (df_kj + df_ki) * sp.exp(-df_ki)
		return result
	
	except:
		# 如果积分失败，使用简化方法
		# 在x=0.5处评估函数
		wkj_mid = wkj.subs(x, 0.5)
		wji_mid = wji.subs(x, 0.5)
		wki_mid = wki.subs(x, 0.5)
		wij_mid = wji.subs(x, 0.5)
		
		df_kj = sp.Abs((wki_mid - wji_mid) / (wki_mid + wji_mid))
		df_ki = sp.Abs((wkj_mid - wij_mid) / (wkj_mid + wij_mid))
		
		return df_kj / (df_kj + df_ki) * sp.exp(-df_ki)


def UEM1_symbolic (k: str, i: str, j: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> Union[
	float, sp.Symbol]:
	"""符号计算版本的UEM1模型"""
	d_ki = _df_UEM1_symbolic(k, i, T, phase_state, order_degree)
	d_kj = _df_UEM1_symbolic(k, j, T, phase_state, order_degree)
	
	# 避免除零
	denominator = d_kj + d_ki
	
	# 使用Piecewise处理条件
	contri_coef_ki = sp.Piecewise(
			(d_kj / denominator * sp.exp(-d_ki), sp.Ne(denominator, 0)),
			(sp.Rational(1, 2), True)
	)
	
	return contri_coef_ki


def GSM_symbolic (k: str, i: str, j: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> Union[
	float, sp.Symbol]:
	"""符号计算版本的GSM模型"""
	beta_kj = _beta_kj_symbolic(k, j, i, T, phase_state, order_degree)
	beta_ki = _beta_kj_symbolic(k, i, j, T, phase_state, order_degree)
	
	# 避免除零
	denominator = beta_ki + beta_kj
	
	# 使用Piecewise处理条件
	result = sp.Piecewise(
			(beta_kj / denominator, sp.Ne(denominator, 0)),
			(sp.Rational(1, 2), True)
	)
	
	return result


def Toop_Kohler_symbolic (k: str, i: str, j: str, T: Union[float, sp.Symbol], phase_state: str, order_degree: str) -> \
Union[float, sp.Symbol]:
	"""符号计算版本的Toop-Kohler模型"""
	asym = _asym_component_choice_symbolic(k, i, j, phase_state, order_degree)
	
	if asym == k:
		return 0
	elif asym == i:
		return 0
	elif asym == j:
		return 1
	else:
		return sp.Rational(1, 2)  # 默认值


# 创建模型函数映射
SYMBOLIC_MODEL_FUNCTIONS = {
	'K': Kohler_symbolic,
	'M': Muggianu_symbolic,
	'T-K': Toop_Kohler_symbolic,
	'GSM': GSM_symbolic,
	'UEM1': UEM1_symbolic,
	'UEM2_N': UEM2_N_symbolic
}


def get_symbolic_model_function (model_name: str) -> extrap_func_symbolic:
	"""获取符号计算版本的模型函数"""
	return SYMBOLIC_MODEL_FUNCTIONS.get(model_name, UEM1_symbolic)


import sympy as sp
from sympy import symbols, exp, log, sqrt, Abs, Piecewise, simplify
from typing import Union, Dict, List, Callable
import math
import itertools


def _get_subBinary_composition_symbolic (comp_dict: Dict[str, Union[float, sp.Symbol]],
                                         T: Union[float, sp.Symbol],
                                         phase_state: str, order_degree: str,
                                         model_func: extrap_func_symbolic,
                                         GeoModel='UEM1') -> List[BinarySymbolic]:
    """符号计算版本的多组分系统中子二元系摩尔组成计算"""
    # 归一化组成
    total = sum(comp_dict.values())
    CompLst = list(comp_dict.keys())
    
    # 归一化
    normalized_comp = {}
    for item in CompLst:
        if isinstance(total, sp.Symbol) or isinstance(total, sp.Expr):
            normalized_comp[item] = comp_dict[item] / total
        else:
            if float(total) != 0:
                normalized_comp[item] = comp_dict[item] / total
            else:
                normalized_comp[item] = comp_dict[item]
    
    # 创建列表存储二元系统
    BinaryList = []
    n = len(CompLst)
    
    # 遍历所有可能的二元组合
    for i in range(n):
        for j in range(i + 1, n):
            A = CompLst[i]
            B = CompLst[j]
            xa = normalized_comp[A]
            xb = normalized_comp[B]
            
            # 创建二元系统
            b_AB = BinarySymbolic(A, B, phase_state=phase_state, order_degree=order_degree)
            b_AB.set_T_symbolic(T)
            
            # 计算其他组分的贡献
            sum_Contri_to_A = 0
            sum_Contri_to_B = 0
            
            for item in CompLst:
                if item != A and item != B:
                    C = item
                    xc = normalized_comp[C]
                    
                    contrib_A = model_func(C, A, B, T, phase_state, order_degree)
                    contrib_B = model_func(C, B, A, T, phase_state, order_degree)
                    
                    sum_Contri_to_A += contrib_A * xc
                    sum_Contri_to_B += contrib_B * xc
            
            # 计算有效组成
            delta_A = xa + sum_Contri_to_A
            delta_B = xb + sum_Contri_to_B
            
            # 设置二元系统中的组成
            b_AB.set_X_symbolic(delta_A, delta_B)
            
            # 添加到列表
            BinaryList.append(b_AB)
    
    return BinaryList


def get_mixingEnthalpy_byMiedema_symbolic (comp_dict: Dict[str, Union[float, sp.Symbol]],
                                           T: Union[float, sp.Symbol],
                                           phase_state: str, order_degree: str,
                                           model_func: extrap_func_symbolic,
                                           GeoModel='UEM1') -> Union[float, sp.Symbol]:
    """符号计算版本的Miedema模型混合焓计算"""
    # 计算子二元组成
    BinaryList = _get_subBinary_composition_symbolic(comp_dict, T, phase_state, order_degree,
                                                     model_func, GeoModel)
    
    # 计算总混合焓
    Total_H = 0
    
    if len(BinaryList) >= 1:
        for bij in BinaryList:
            Xi = bij.xA
            Xj = bij.xB
            i, j = bij.A.symbol, bij.B.symbol
            xi, xj = comp_dict[i], comp_dict[j]
            
            # 计算二元系对总焓的贡献
            binary_enthalpy = bij.getEnthalpy_byMiedema_Model_symbolic(Xi, Xj)
            
            # 使用Piecewise避免除零
            contribution = sp.Piecewise(
                    (xi * xj * binary_enthalpy / (Xi * Xj), sp.And(sp.Ne(Xi, 0), sp.Ne(Xj, 0))),
                    (0, True)
            )
            
            Total_H += contribution
    
    return Total_H


def get_Gibbs_byMiedema_symbolic (comp_dict: Dict[str, Union[float, sp.Symbol]],
                                  T: Union[float, sp.Symbol],
                                  phase_state: str, order_degree: str,
                                  model_func: extrap_func_symbolic,
                                  GeoModel='UEM1') -> Union[float, sp.Symbol]:
    """符号计算版本的Miedema模型吉布斯自由能计算"""
    # 计算子二元组成
    BinaryList = _get_subBinary_composition_symbolic(comp_dict, T, phase_state, order_degree,
                                                     model_func=model_func, GeoModel=GeoModel)
    
    # 计算总过量吉布斯能量
    gE = 0
    
    if len(BinaryList) >= 1:
        for bij in BinaryList:
            Xi = bij.xA
            Xj = bij.xB
            i, j = bij.A.symbol, bij.B.symbol
            xi, xj = comp_dict[i], comp_dict[j]
            
            # 计算二元系对总吉布斯能量的贡献
            binary_gibbs = bij.get_excess_Gibbs_symbolic(Xi, Xj)
            
            # 使用Piecewise避免除零
            contribution = sp.Piecewise(
                    (xi * xj * binary_gibbs / (Xi * Xj), sp.And(sp.Ne(Xi, 0), sp.Ne(Xj, 0))),
                    (0, True)
            )
            
            gE += contribution
    
    # 计算理想混合熵
    entropy_ideal = 0
    for element, x_i in comp_dict.items():
        if isinstance(x_i, (sp.Symbol, sp.Expr)):
            # 符号情况，使用Piecewise处理log(0)
            entropy_contrib = sp.Piecewise(
                    (-x_i * sp.log(x_i), sp.And(sp.re(x_i) > 0, sp.im(x_i) == 0)),
                    (0, True)
            )
        else:
            # 数值情况
            if float(x_i) > 1e-10:
                entropy_contrib = -float(x_i) * math.log(float(x_i))
            else:
                entropy_contrib = 0
        entropy_ideal += entropy_contrib
    
    # 单位转换：J/(mol·K) 到 kJ/(mol·K)
    entropy_ideal = entropy_ideal * 8.314 / 1000
    
    # 计算总吉布斯自由能
    gibbs_free_energy = gE - T * entropy_ideal
    
    return gibbs_free_energy


def _gmE_symbolic (Tem: Union[float, sp.Symbol], phase_state: str, order_degree: str,
                   model_func: extrap_func_symbolic, GeoModel: str,
                   *args) -> Union[float, sp.Symbol]:
    """符号计算版本的摩尔吉布斯自由能函数"""
    comp_dict = {}
    for kvp in args:
        comp_dict[kvp[0]] = kvp[1]
    
    return get_Gibbs_byMiedema_symbolic(comp_dict, T=Tem, phase_state=phase_state,
                                        order_degree=order_degree, model_func=model_func,
                                        GeoModel=GeoModel)


# 气体常数
GAS_CONSTANT_R_kJ = 8.314e-3  # kJ/(mol·K)


def calculate_activity_coefficient_symbolic (
        comp_dict: Dict[str, Union[float, sp.Symbol]],
        solute_i: str,
        solvent: str,
        temperature: Union[float, sp.Symbol],
        phase_state: str,
        order_degree: str,
        model_func: extrap_func_symbolic,
        geo_model: str = 'UEM1'
) -> Union[float, sp.Symbol]:
    """符号计算版本的活度系数计算"""
    
    if solute_i not in comp_dict or solvent not in comp_dict:
        raise ValueError("溶质或溶剂不在组成中")
    
    # 提取组分并验证摩尔分数
    other_components = [c for c in comp_dict if c not in {solute_i, solvent}]
    x_i = comp_dict[solute_i]
    x_others = [comp_dict[c] for c in other_components]
    
    # 创建符号变量
    sym_i = sp.Symbol(f'x_{solute_i}', real=True, positive=True)
    sym_others = [sp.Symbol(f'x_{c}', real=True, positive=True) for c in other_components]
    
    # 符号溶剂摩尔分数
    sym_solvent = 1 - sym_i - sum(sym_others)
    
    # 创建数值替换字典
    subs_dict = {sym_i: x_i}
    subs_dict.update({sym: val for sym, val in zip(sym_others, x_others)})
    
    # 准备组分元组
    symbolic_comp_tuples = [(solute_i, sym_i)]
    symbolic_comp_tuples.extend([(c, s) for c, s in zip(other_components, sym_others)])
    symbolic_comp_tuples.append((solvent, sym_solvent))
    
    # 计算符号过量吉布斯能量
    gm_excess_sym = _gmE_symbolic(
            temperature, phase_state, order_degree, model_func, geo_model,
            *symbolic_comp_tuples
    )
    
    # 计算理想混合部分
    ideal_part = 0
    for element, x_sym in [(solute_i, sym_i)] + list(zip(other_components, sym_others)) + [(solvent, sym_solvent)]:
        ideal_contrib = sp.Piecewise(
                (-x_sym * sp.log(x_sym), sp.And(sp.re(x_sym) > 0, sp.im(x_sym) == 0)),
                (0, True)
        )
        ideal_part += ideal_contrib
    
    ideal_part = ideal_part * GAS_CONSTANT_R_kJ * temperature
    
    # 总吉布斯自由能
    gm_total_sym = gm_excess_sym - ideal_part
    
    # 计算偏导数 ∂G/∂n_i
    dG_dni = sp.diff(gm_total_sym, sym_i)
    
    # 计算其他组分的偏导数
    dG_dnothers = [sp.diff(gm_total_sym, sym) for sym in sym_others]
    
    # 计算偏摩尔吉布斯自由能
    # μ_i = G + (1-x_i) * ∂G/∂x_i - Σ(x_k * ∂G/∂x_k) for k≠i
    mu_i_excess = gm_excess_sym + (1 - sym_i) * sp.diff(gm_excess_sym, sym_i)
    
    # 减去其他组分的贡献
    for k, (x_k, dG_dk) in enumerate(zip(x_others, [sp.diff(gm_excess_sym, sym) for sym in sym_others])):
        mu_i_excess -= x_k * dG_dk
    
    # 替换数值
    mu_i_excess_val = mu_i_excess.subs(subs_dict)
    
    # 计算活度系数 ln(γ_i) = μ_i^E / (RT)
    ln_gamma_i = mu_i_excess_val / (GAS_CONSTANT_R_kJ * temperature)
    
    return ln_gamma_i


def calculate_activity_symbolic (comp_dict: Dict[str, Union[float, sp.Symbol]],
                                 solute_i: str, solvent: str,
                                 temperature: Union[float, sp.Symbol],
                                 phase_state: str, order_degree: str,
                                 model_func: extrap_func_symbolic,
                                 geo_model: str = 'UEM1') -> Union[float, sp.Symbol]:
    """符号计算版本的活度计算"""
    ln_gamma_i = calculate_activity_coefficient_symbolic(
            comp_dict, solute_i, solvent, temperature, phase_state, order_degree,
            model_func, geo_model
    )
    
    x_i = comp_dict[solute_i]
    gamma_i = sp.exp(ln_gamma_i)
    activity = x_i * gamma_i
    
    return activity


# 数值评估函数
def evaluate_symbolic_result (symbolic_expr: Union[float, sp.Symbol],
                              substitutions: Dict = None) -> float:
    """将符号表达式转换为数值结果"""
    if isinstance(symbolic_expr, (int, float)):
        return float(symbolic_expr)
    
    if substitutions:
        symbolic_expr = symbolic_expr.subs(substitutions)
    
    try:
        # 尝试直接评估
        result = float(symbolic_expr.evalf())
        return result
    except:
        # 如果失败，尝试简化后评估
        try:
            simplified = sp.simplify(symbolic_expr)
            result = float(simplified.evalf())
            return result
        except:
            # 如果仍然失败，抛出错误
            raise ValueError(f"无法将符号表达式转换为数值: {symbolic_expr}")


# 混合接口函数（自动选择符号或数值计算）
def calculate_activity_coefficient_auto (comp_dict, solute_i, solvent, temperature,
                                         phase_state, order_degree, model_func, geo_model='UEM1'):
    """自动选择符号或数值计算的活度系数函数"""
    # 检查是否包含符号变量
    has_symbols = any(isinstance(v, (sp.Symbol, sp.Expr)) for v in comp_dict.values()) or \
                  isinstance(temperature, (sp.Symbol, sp.Expr))
    
    if has_symbols:
        # 使用符号计算
        symbolic_model_func = get_symbolic_model_function(
            model_func.__name__ if hasattr(model_func, '__name__') else 'UEM1')
        return calculate_activity_coefficient_symbolic(
                comp_dict, solute_i, solvent, temperature, phase_state, order_degree,
                symbolic_model_func, geo_model
        )
    else:
        # 使用数值计算
        symbolic_model_func = get_symbolic_model_function(
            model_func.__name__ if hasattr(model_func, '__name__') else 'UEM1')
        result = calculate_activity_coefficient_symbolic(
                comp_dict, solute_i, solvent, temperature, phase_state, order_degree,
                symbolic_model_func, geo_model
        )
        return evaluate_symbolic_result(result)


def calculate_activity_auto (comp_dict, solute_i, solvent, temperature,
                             phase_state, order_degree, model_func, geo_model='UEM1'):
    """自动选择符号或数值计算的活度函数"""
    # 检查是否包含符号变量
    has_symbols = any(isinstance(v, (sp.Symbol, sp.Expr)) for v in comp_dict.values()) or \
                  isinstance(temperature, (sp.Symbol, sp.Expr))
    
    if has_symbols:
        # 使用符号计算
        symbolic_model_func = get_symbolic_model_function(
            model_func.__name__ if hasattr(model_func, '__name__') else 'UEM1')
        return calculate_activity_symbolic(
                comp_dict, solute_i, solvent, temperature, phase_state, order_degree,
                symbolic_model_func, geo_model
        )
    else:
        # 使用数值计算
        symbolic_model_func = get_symbolic_model_function(
            model_func.__name__ if hasattr(model_func, '__name__') else 'UEM1')
        result = calculate_activity_symbolic(
                comp_dict, solute_i, solvent, temperature, phase_state, order_degree,
                symbolic_model_func, geo_model
        )
        return evaluate_symbolic_result(result)