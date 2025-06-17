import itertools
import math
import os
from typing import Callable
from scipy.integrate import quad
from sympy import *
from mpmath import mp
from . import BinarySys as Bin_Miedema
import sympy as sp
from typing import Dict, List, Tuple, Callable, Any # Use Any for the unknown model_func structure for now



def exp (x):
	return math.exp(x)


def _asym_component_choice (k: str, i: str, j: str, phase_state: str, order_degree: str):
	'''Implementation of Qiao's asymmetric component selection rule
    
    Args:
        k (str): Element symbol for component k
        i (str): Element symbol for component i
        j (str): Element symbol for component j
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering, 'SS', 'AMP', or 'IM'
    
    Returns:
        str: Selected component symbol
    '''
	# Calculate binary enthalpies
	bij = Bin_Miedema.Binary(i, j, phase_state=phase_state, order_degree=order_degree)
	bik = Bin_Miedema.Binary(i, k, phase_state=phase_state, order_degree=order_degree)
	bjk = Bin_Miedema.Binary(j, k, phase_state=phase_state, order_degree=order_degree)
	
	a = bij.getEnthalpy_byMiedema_Model(0.5, 0.5)
	b = bik.getEnthalpy_byMiedema_Model(0.5, 0.5)
	c = bjk.getEnthalpy_byMiedema_Model(0.5, 0.5)
	
	# Apply selection rule
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


def _beta_kj (k: str, j: str, i: str, T: float, phase_state: str, order_degree: str):
	'''Calculate deviation function in Chou's model (beta_k-j)
    
    Args:
        k (str): Element symbol for component k
        j (str): Element symbol for component j
        i (str): Element symbol for component i
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
    
    Returns:
        float: Beta value
    '''
	# Define integration function
	bik = Bin_Miedema.Binary(i, k, phase_state=phase_state, order_degree=order_degree)
	bij = Bin_Miedema.Binary(i, j, phase_state=phase_state, order_degree=order_degree)
	bik.set_T(Tem=T)
	bij.set_T(Tem=T)
	
	def func_yeta (x):
		return (bik.get_excess_Gibbs(x, 1.0 - x) -
		        bij.get_excess_Gibbs(x, 1.0 - x))
	
	def func_yeta2 (x):
		return func_yeta(x) * func_yeta(x)
	
	# Perform numerical integration
	result = quad(func_yeta2, 0, 1)[0]
	return result


def _df_UEM1 (k: str, i: str, T: float, phase_state: str, order_degree: str):
	'''Calculate property difference for UEM1 model
    
    Args:
        k (str): Element symbol for component k
        i (str): Element symbol for component i
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
    
    Returns:
        float: Property difference value
    '''
	bik = Bin_Miedema.Binary(i, k, phase_state=phase_state, order_degree=order_degree)
	bik.set_T(Tem=T)
	lnYi0 = bik.d_fun10()
	lnYk0 = bik.d_fun20()
	return abs(lnYk0 - lnYi0)


def UEM2_N (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
	'''Calculate interaction property difference for UEM2 model
    
    Args:
        k (str): Element symbol for component k
        i (str): Element symbol for component i
        j (str): Element symbol for component j
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
    
    Returns:
        float: Property difference value
    '''
	# Define integration functions for average Gibbs energy
	bij = Bin_Miedema.Binary(i, j, phase_state=phase_state, order_degree=order_degree)
	bkj = Bin_Miedema.Binary(k, j, phase_state=phase_state, order_degree=order_degree)
	bij.set_T(Tem=T)
	bkj.set_T(Tem=T)
	bji = Bin_Miedema.Binary(j, i, phase_state=phase_state, order_degree=order_degree)
	bki = Bin_Miedema.Binary(k, i, phase_state=phase_state, order_degree=order_degree)
	bji.set_T(Tem=T)
	bki.set_T(Tem=T)
	
	def wij (x):
		return bij.get_excess_Gibbs(x, 1 - x)
	
	def wkj (x):
		return bkj.get_excess_Gibbs(x, 1 - x)
	
	def wji (x):
		return bji.get_excess_Gibbs(x, 1 - x)
	
	def wki (x):
		return bki.get_excess_Gibbs(x, 1 - x)
	
	Wkj = quad(wkj, 0, 1)[0]
	Wji = quad(wji, 0, 1)[0]
	Wki = quad(wki, 0, 1)[0]
	Wij = quad(wji, 0, 1)[0]
	
	df_kj = abs((Wki - Wji) / (Wki + Wji))
	df_ki = abs((Wkj - Wij) / (Wkj + Wij))
	
	return df_kj / (df_kj + df_ki) * exp(-df_ki)


def Kohler (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
	return 0


def Muggianu (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
	return 0.5


def UEM1 (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
	d_ki = _df_UEM1(k, i, T, phase_state, order_degree)
	d_kj = _df_UEM1(k, j, T, phase_state, order_degree)
	
	# Avoid division by zero
	denominator = d_kj + d_ki
	if abs(denominator) < 1e-10:
		return 0.5
	
	contri_coef_ki = d_kj / denominator * exp(-d_ki)
	return contri_coef_ki


def GSM (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
	beta_kj = _beta_kj(k, j, i, T, phase_state, order_degree)
	beta_ki = _beta_kj(k, i, j, T, phase_state, order_degree)
	
	# Avoid division by zero
	denominator = beta_ki + beta_kj
	if abs(denominator) < 1e-10:
		return 0.5
	
	return beta_kj / denominator


def Toop_Kohler (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
	asym = _asym_component_choice(k, i, j, phase_state, order_degree)
	
	if asym == k:
		return 0.0
	if asym == i:
		return 0.0
	if asym == j:
		return 1.0


# 定义一个函数类型：接受6个特定类型参数并返回float
extrap_func = Callable[[str, str, str, float, str, str], float]


def _get_subBinary_composition (comp_dict: dict, T: float, phase_state: str, order_degree: str, model_func: extrap_func,
                                GeoModel='UEM1'):
	'''Calculate molar composition of sub-binary systems in multi-component system
    
    Args:
        comp_dict (dict): Dictionary of element compositions {element_symbol: mole_fraction}
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
        
    
    Returns:
        list: List of Binary objects with calculated compositions
    '''
	# Normalize compositions
	N = sum(comp_dict.values())
	CompLst = list(comp_dict.keys())
	
	if N != 0:
		for item in CompLst:
			comp_dict[item] = comp_dict[item] / N
	
	# Create list to store binary systems
	BinaryList = []
	n = len(CompLst)
	
	# Iterate through all possible binary combinations
	for i in range(n):
		for j in range(i + 1, n):
			A = CompLst[i]
			B = CompLst[j]
			xa = comp_dict[A]
			xb = comp_dict[B]
			
			# Create binary system
			b_AB = Bin_Miedema.Binary(A, B, phase_state=phase_state, order_degree=order_degree)
			
			# Calculate contribution quannty by different models
			sum_Contri_to_A, sum_Contri_to_B = 0, 0
			for item in CompLst:
				if item != A and item != B:
					C = item
					xc = comp_dict[C]
					sum_Contri_to_A += model_func(C, A, B, T, phase_state, order_degree) * xc
					sum_Contri_to_B += model_func(C, B, A, T, phase_state, order_degree) * xc
			
			# Calculate effective compositions
			delta_A = xa + sum_Contri_to_A
			delta_B = xb + sum_Contri_to_B
			
			# Set compositions in binary system
			b_AB.set_X(delta_A, delta_B)
			
			# Add to list
			BinaryList.append(b_AB)
	
	return BinaryList


def get_mixingEnthalpy_byMiedema (comp_dict: dict, T: float, phase_state: str, order_degree: str,
                                  model_func: extrap_func, GeoModel='UEM1'):
	'''Calculate mixing enthalpy of multi-component system using Miedema model with extrapolation
    
    Args:
        comp_dict (dict): Dictionary of element compositions {element_symbol: mole_fraction}
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
      
    
    Returns:
        float: Mixing enthalpy in kJ/mol
    '''
	# Calculate sub-binary compositions
	BinaryList: list[Bin_Miedema.Binary] = _get_subBinary_composition(comp_dict, T, phase_state, order_degree,
	                                                                  model_func, GeoModel)
	
	#BinaryList = _get_subBinary_composition(comp_dict, T, phase_state, order_degree, model_func,GeoModel)
	
	# Calculate total mixing enthalpy
	Total_H = 0
	
	if len(BinaryList) >= 1:
		for bij in BinaryList:
			Xi = bij.xA
			Xj = bij.xB
			i, j = bij.A.symbol, bij.B.symbol
			xi, xj = comp_dict[i], comp_dict[j]
			
			# Calculate binary contribution to total enthalpy
			binary_enthalpy = bij.getEnthalpy_byMiedema_Model(Xi, Xj)
			
			if Xi > 0.0 and Xj > 0.0:
				Total_H += xi * xj / (Xi * Xj) * binary_enthalpy
	
	return Total_H


def get_Gibbs_byMiedema (comp_dict: dict, T: float, phase_state: str, order_degree: str, model_func: extrap_func,
                         GeoModel='UEM1'):
	'''Calculate Gibbs free energy of multi-component system using Miedema model with extrapolation
    
    Args:
        comp_dict (dict): Dictionary of element compositions {element_symbol: mole_fraction}
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
      
    
    Returns:
        float: Gibbs free energy in kJ/mol
    '''
	# Calculate sub-binary compositions
	BinaryList: list[Bin_Miedema.Binary] = _get_subBinary_composition(comp_dict, T, phase_state, order_degree,
	                                                                  model_func=model_func, GeoModel=GeoModel)
	
	# Calculate total excess Gibbs energy
	gE = 0
	
	if len(BinaryList) >= 1:
		for bij in BinaryList:
			Xi = bij.xA
			Xj = bij.xB
			i, j = bij.A.symbol, bij.B.symbol
			xi, xj = comp_dict[i], comp_dict[j]
			bij.set_T(T)
			# Calculate binary contribution to total Gibbs energy
			
			binary_gibbs = bij.get_excess_Gibbs(Xi, Xj)
			if Xi > 0.0 and Xj > 0.0:
				gE += xi * xj / (Xi * Xj) * binary_gibbs
	entropy_ideal = -8.314 * sum([comp_dict[i] * math.log(comp_dict[i]) / 1000 for i in comp_dict if comp_dict[i] > 0])
	gibbs_free_energy: float = gE - T * entropy_ideal
	return gibbs_free_energy


def _gmE (Tem: float, phase_state: str, order_degree: str, model_func: extrap_func, GeoModel: str,
          *args: tuple[str, float]):
	'''摩尔吉布斯自由能函数'''
	comp_dict = dict()
	for kvp in args:
		comp_dict.update({kvp[0]: kvp[1]})
	return get_Gibbs_byMiedema(comp_dict, T=Tem, phase_state=phase_state, order_degree=order_degree,
	                           model_func=model_func, GeoModel=GeoModel)


#计算活度系数
# Define constants
GAS_CONSTANT_R = 8.3145  # J / (mol * K)


# Assume _gmE is defined elsewhere or imported, e.g.:
# from .thermo_models import _gmE
# Since its signature isn't provided, we'll assume it takes:
# temperature, phase_state, order_degree, model_func, geo_model, *component_tuples
# where component_tuples are like (name, mole_fraction_or_symbol)

import sympy as sp
from typing import Dict, Callable
from scipy.constants import R  # GAS_CONSTANT_R in J/(mol·K)


#活度系数计算公式，
def calculate_activity_coefficient (
		comp_dict: Dict[str, float],
		solute_i: str,
		solvent: str,
		temperature: float,
		phase_state: str,
		order_degree: str,
		model_func: Callable,
		geo_model: str = 'UEM1'
) -> float:
	"""
	使用有限差分法计算活度系数
	ln(γ_i) = (∂G^E/∂x_i) / (RT)
	"""
	# 输入验证
	if solute_i not in comp_dict or solvent not in comp_dict:
		raise ValueError(f"溶质 {solute_i} 或溶剂 {solvent} 不在组成中")
	if temperature <= 0:
		raise ValueError("温度必须大于0")
	
	# 归一化组成
	total = sum(comp_dict.values())
	if abs(total - 1.0) > 1e-6:
		comp_dict = {k: v / total for k, v in comp_dict.items()}
	
	# 获取溶质的摩尔分数
	x_i = comp_dict[solute_i]
	
	# 定义微小增量
	delta = min(1e-6, x_i * 0.01, (1.0 - x_i) * 0.01)
	
	# 创建微扰组成
	def create_perturbed_composition (dx):
		perturbed = comp_dict.copy()
		perturbed[solute_i] += dx
		
		# 确保组成和为1，按比例调整其他组分
		excess = perturbed[solute_i] + sum(v for k, v in perturbed.items() if k != solute_i) - 1.0
		
		# 从其他组分中按比例减去多余部分
		other_sum = sum(v for k, v in perturbed.items() if k != solute_i)
		if other_sum > excess and excess > 0:
			for k in perturbed:
				if k != solute_i:
					perturbed[k] -= excess * perturbed[k] / other_sum
		
		# 确保所有组分都是非负的
		for k in perturbed:
			if perturbed[k] < 0:
				perturbed[k] = 1e-10
		
		# 最终归一化
		total_final = sum(perturbed.values())
		return {k: v / total_final for k, v in perturbed.items()}
	
	try:
		# 计算 G(x_i + δ) 和 G(x_i - δ)
		comp_plus = create_perturbed_composition(delta)
		comp_minus = create_perturbed_composition(-delta)
		
		# 计算吉布斯自由能
		G_plus = get_Gibbs_byMiedema(comp_plus, temperature, phase_state,
		                             order_degree, model_func, geo_model)
		G_minus = get_Gibbs_byMiedema(comp_minus, temperature, phase_state,
		                              order_degree, model_func, geo_model)
		
		# 计算偏导数 ∂G/∂x_i
		dG_dxi = (G_plus - G_minus) / (2 * delta)
		
		# 计算活度系数 ln(γ_i) = (∂G/∂x_i - ∂G/∂x_j) / (RT)
		# 这里我们使用简化形式：ln(γ_i) = ∂G^E/∂x_i / (RT)
		
		# 为了得到过量部分，我们减去理想混合的贡献
		# ∂G_ideal/∂x_i = RT * (ln(x_i) + 1)
		R_kJ = 8.314e-3  # kJ/(mol·K)
		
		if x_i > 1e-10:
			dG_ideal_dxi = R_kJ * temperature * (math.log(x_i) + 1)
		else:
			dG_ideal_dxi = R_kJ * temperature * (-23 + 1)  # ln(1e-10) ≈ -23
		
		# 过量部分的偏导数
		dG_excess_dxi = dG_dxi - dG_ideal_dxi
		
		# 活度系数
		ln_gamma_i = dG_excess_dxi / (R_kJ * temperature)
		
		return float(ln_gamma_i)
	except:
		pass

#活度计算
def calculate_activity (comp_dict: dict, solutei: str, solvent: str, Tem: float, phase_state: str, order_degree: str,
                   model_func: extrap_func, GeoModel='UEM1'):
	'''
	活度计算，组分i的活度
	@param Tem:温度
	'''
	lnyi = calculate_activity_coefficient(comp_dict, solutei, solvent, Tem, phase_state, order_degree, model_func,
	                                      GeoModel)
	xi = comp_dict[solutei]
	return xi * math.exp(lnyi)





def format_decimal (num):
	"""
    格式化小数：
    - 如果小数位超过3位，则保留3位小数
    - 如果小数位少于或等于3位，则保持原样
    """
	# 转换为字符串以检查小数位数
	str_num = str(float(num))
	
	# 检查是否有小数点
	if '.' in str_num:
		integer_part, decimal_part = str_num.split('.')
		# 如果小数部分长度大于3，保留3位小数
		if len(decimal_part) > 3:
			return round(num, 3)
	
	# 否则保持原样
	return num


def _print_Contri_Coefficient (k: str, i: str, j: str, T: float, phase_state: str, order_degree: str,
                               model_func: extrap_func, Gemodel: list, fileName: str):
	'''Print contribution coefficients to file
    
    Args:
        k (str): Element symbol for component k
        i (str): Element symbol for component i
        j (str): Element symbol for component j
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
        GeoModel (str): Extrapolation model
    '''
	# Calculate contribution coefficients
	Aki = format_decimal(model_func(k, i, j, T, phase_state, order_degree))
	Akj = format_decimal(model_func(k, j, i, T, phase_state, order_degree))
	Aij = format_decimal(model_func(i, j, k, T, phase_state, order_degree))
	Aji = format_decimal(model_func(j, i, k, T, phase_state, order_degree))
	Aik = format_decimal(model_func(i, k, j, T, phase_state, order_degree))
	Ajk = format_decimal(model_func(j, k, i, T, phase_state, order_degree))
	
	# Create directory if not exists
	current_dir = os.path.dirname(os.path.abspath(__file__))
	dir1 = os.path.join(current_dir, "contribution_Coefficient", "Miedema-model")
	os.makedirs(dir1, exist_ok=True)
	
	# Determine file name based on model
	
	for geomodel in Gemodel:
		filename = fileName + r'(' + geomodel.replace("/", "-") + ').txt'
		filepath = os.path.join(dir1, filename)
		file_exists = os.path.exists(filepath)
		with open(filepath, "a") as f:
			if not file_exists:
				header = f"k-i：alpha^k_i(ij) \t\t k-j ：alpha^k_j(ij)\n"
				f.write(header)
			
			f.write(f'{k}-{i}:\t{Aki},\t{k}-{j}:\t{Akj}\tin\t{i}-{j}\n')
			f.write(f'{i}-{k}:\t{Aik},\t{i}-{j}:\t{Aij}\tin\t{k}-{j}\n')
			f.write(f'{j}-{i}:\t{Aji},\t{j}-{k}:\t{Ajk}\tin\t{i}-{k}\n')


def print_Contri_Coeff (compositions: dict, T: float, phase_state: str, order_degree: str, model_func: extrap_func,
                        GeoModel: list):
	keys = list(compositions.keys())
	key_combinations = list(itertools.combinations(keys, 3))
	for key_combination in key_combinations:
		k1, i1, j1 = key_combination
		fileName = f'{k1}-{i1}-{j1}-{T}'
		_print_Contri_Coefficient(k1, i1, j1, T, phase_state, order_degree, model_func, GeoModel, fileName)
