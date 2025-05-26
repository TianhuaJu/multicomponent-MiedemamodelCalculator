import sympy as sp
from sympy import symbols, exp, log, sqrt, Abs, Piecewise, simplify
import math
import os
import sqlite3 as sq
from typing import Union, Dict, List, Tuple
import time


class ElementSymbolic:
	"""符号计算版本的Element类"""
	
	def __init__ (self, A: str) -> None:
		"""初始化元素类并从数据库获取元素属性"""
		table = "Miedema1983"
		self._querydata(A, table)
	
	def _querydata (self, A: str, table: str):
		"""连接数据库并检索数据"""
		try:
			# 确定数据库路径
			current_dir = os.path.dirname(os.path.abspath(__file__))
			db_path = os.path.join(current_dir, "BinaryData", "Miedema_physical_parmeter.db")
			
			conn = sq.connect(db_path)
			cursor = conn.cursor()
			cmdTxt = 'SELECT phi, nws, V, u, alpha_beta, hybirdvalue, isTrans, ' \
			         'dHtrans, mass, Tm, Tb, name FROM ' + table + ' WHERE Symbol = ?'
			cursor_result = cursor.execute(cmdTxt, (A,))
			data = cursor_result.fetchall()
			
			if not data:
				raise Exception(f"Element {A} not found in database.")
			
			data = data[0]
			
			self.phi = float(data[0])
			self.nws = float(data[1])
			self.V = float(data[2])
			self.u = float(data[3])
			self.alpha_beta = data[4]
			self.hybirdvalue = float(data[5])
			self.isTrans = bool(data[6])
			self.dHtrans = float(data[7])
			self.mass = float(data[8])
			self.Tm = float(data[9])
			self.Tb = float(data[10])
			self.name = data[11]
			self.symbol = A
			
			conn.close()
		except Exception as e:
			raise Exception(f"Error querying database for element {A}: {str(e)}")


class BinarySymbolic:
	"""符号计算版本的Binary系统类"""
	
	def __init__ (self, A: str, B: str, phase_state: str, order_degree='IM'):
		"""初始化二元系统"""
		self.lammda = 0.0
		self.A = ElementSymbolic(A)
		self.B = ElementSymbolic(B)
		self.xA = sp.Symbol(f'x_{A}', real=True, positive=True)
		self.xB = sp.Symbol(f'x_{B}', real=True, positive=True)
		self.Tem = sp.Symbol('T', real=True, positive=True)
		
		# 设置alpha基于相态
		if phase_state == 'S':
			self.alpha = 1.0
		elif phase_state == 'L':
			self.alpha = 0.73
		else:
			raise ValueError(f"Invalid phase_state: {phase_state}. Must be 'S' or 'L'.")
		
		# 设置lambda基于有序度
		if order_degree == 'SS':
			self.lammda = 0.0
		elif order_degree == 'AMP':
			self.lammda = 5.0
		elif order_degree == 'IM':
			self.lammda = 8.0
		else:
			raise ValueError(f"Invalid order_degree: {order_degree}. Must be 'SS', 'AMP', or 'IM'.")
	
	def set_X_symbolic (self, xA: Union[float, sp.Symbol], xB: Union[float, sp.Symbol]):
		"""设置二元系统的符号组成"""
		total = xA + xB
		self.xA = xA / total
		self.xB = xB / total
	
	def set_T_symbolic (self, Tem: Union[float, sp.Symbol]):
		"""设置温度（符号或数值）"""
		self.Tem = Tem
	
	def _V_in_alloy_symbolic (self, xA: Union[float, sp.Symbol], xB: Union[float, sp.Symbol]):
		"""符号计算合金中元素的体积"""
		A = self.A
		B = self.B
		
		# 初始体积
		V1a_sym = sp.Symbol('V1a', real=True, positive=True)
		V2a_sym = sp.Symbol('V2a', real=True, positive=True)
		
		# 使用符号迭代公式
		V1a_init = A.V
		V2a_init = B.V
		
		# 计算体积分数
		Pax = xA * V1a_init / (xB * V2a_init + xA * V1a_init)
		Pbx = xB * V2a_init / (xB * V2a_init + xA * V1a_init)
		
		# 更新体积（符号形式）
		V1a_final = A.V * (1.0 + A.u * Pbx * (1.0 + self.lammda * (Pax * Pbx) ** 2) * (A.phi - B.phi))
		V2a_final = B.V * (1.0 + B.u * Pax * (1.0 + self.lammda * (Pax * Pbx) ** 2) * (B.phi - A.phi))
		
		return V1a_final, V2a_final
	
	def getEnthalpy_byMiedema_Model_symbolic (self, xA: Union[float, sp.Symbol], xB: Union[float, sp.Symbol]):
		"""使用Miedema模型计算形成焓的符号版本"""
		element_A = self.A
		element_B = self.B
		
		# 归一化摩尔分数
		total = xA + xB
		x1 = xA / total
		x2 = xB / total
		
		# 计算r_to_p（杂化贡献）
		r_to_p = 0.0
		if element_A.alpha_beta != "other" and element_B.alpha_beta != "other":
			if element_A.alpha_beta != element_B.alpha_beta:
				r_to_p = self.alpha * element_A.hybirdvalue * element_B.hybirdvalue
		
		# 根据过渡金属状态确定p_AB
		if element_A.isTrans and element_B.isTrans:
			p_AB = 14.2
		elif element_A.isTrans or element_B.isTrans:
			p_AB = 12.35
		else:
			p_AB = 10.7
		
		# 计算化学势差
		df = 2.0 * p_AB * (
				-(element_A.phi - element_B.phi) ** 2 + 9.4 * (element_A.nws - element_B.nws) ** 2 - r_to_p
		) / (1.0 / element_A.nws + 1.0 / element_B.nws)
		
		# 计算合金中的体积
		V_Aa, V_Ba = self._V_in_alloy_symbolic(xA=xA, xB=xB)
		
		# 计算浓度因子
		cAs = x1 * V_Aa / (x1 * V_Aa + x2 * V_Ba)
		cBs = x2 * V_Ba / (x1 * V_Aa + x2 * V_Ba)
		
		# 计算界面浓度函数
		fC = (cAs * cBs * (1.0 + self.lammda * (cAs * cBs) ** 2)) * (x1 * V_Aa + x2 * V_Ba)
		
		# 计算转变焓贡献
		dH_trans = x1 * element_A.dHtrans + x2 * element_B.dHtrans
		
		# 计算总焓
		total_enthalpy = fC * df + dH_trans
		
		return total_enthalpy
	
	def _get_excess_entropy_symbolic (self, xA: Union[float, sp.Symbol], xB: Union[float, sp.Symbol]):
		"""使用Tanaka过量熵关系计算过量熵的符号版本"""
		element_A = self.A
		element_B = self.B
		
		# 计算混合焓
		Hmix = self.getEnthalpy_byMiedema_Model_symbolic(xA=xA, xB=xB)
		
		# 基于相态计算过量熵
		if self.alpha == 0.73:
			excess_entropy = Hmix / 14 * (1.0 / element_A.Tm + 1.0 / element_B.Tm)
		else:
			excess_entropy = Hmix / 15.1 * (1.0 / element_A.Tm + 1.0 / element_B.Tm)
		
		return excess_entropy
	
	def get_excess_Gibbs_symbolic (self, xA: Union[float, sp.Symbol], xB: Union[float, sp.Symbol]):
		"""计算二元合金过量吉布斯自由能的符号版本"""
		# 计算焓和熵贡献
		enthalpy = self.getEnthalpy_byMiedema_Model_symbolic(xA=xA, xB=xB)
		entropy = self._get_excess_entropy_symbolic(xA=xA, xB=xB)
		
		# 计算过量吉布斯自由能
		g_E = enthalpy - self.Tem * entropy
		
		return g_E
	
	def d_fun10_symbolic (self):
		"""计算A在A-B二元合金中温度Tem下稀释时的偏摩尔过量吉布斯自由能的符号版本"""
		A = self.A
		B = self.B
		Tem = self.Tem
		
		# 特殊元素列表
		special_element = ["Si", "Ge", "C", "P"]
		
		# 基于相态设置参数
		dH_trans = 0.0
		entropy_contri_factor = 0.0
		
		if self.alpha == 0.73:
			if self.A.symbol in special_element:
				dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 14.0 * (1.0 / A.Tm + 1.0 / B.Tm)
		else:
			dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 15.2 * (1.0 / A.Tm + 1.0 / B.Tm)
		
		# 计算杂化贡献
		r_to_p = 0.0
		if A.alpha_beta != "other" and B.alpha_beta != "other":
			if A.alpha_beta != B.alpha_beta:
				r_to_p = self.alpha * A.hybirdvalue * B.hybirdvalue
		
		# 根据过渡金属状态确定p_AB
		if A.isTrans and B.isTrans:
			p_AB = 14.2
		elif A.isTrans or B.isTrans:
			p_AB = 12.35
		else:
			p_AB = 10.7
		
		# 计算化学势差
		df = 2.0 * p_AB * (-(A.phi - B.phi) ** 2 + 9.4 * (A.nws - B.nws) ** 2 - r_to_p) \
		     / (1.0 / A.nws + 1.0 / B.nws)
		
		# 计算ln(Y0)
		lnY0 = 1000.0 * df * B.V * (1.0 + B.u * (B.phi - A.phi)) / (8.314 * Tem) + 1000.0 * dH_trans / (8.314 * Tem)
		
		return lnY0 * (1.0 - entropy_contri_factor)
	
	def d_fun20_symbolic (self):
		"""计算B在A-B二元合金中温度Tem下稀释时的偏摩尔过量吉布斯自由能的符号版本"""
		# 交换A和B的角色
		A = self.B
		B = self.A
		Tem = self.Tem
		
		# 特殊元素列表
		special_element = ["Si", "Ge", "C", "P"]
		
		# 基于相态设置参数
		dH_trans = 0.0
		entropy_contri_factor = 0.0
		
		if self.alpha == 0.73:
			if self.A.symbol in special_element:
				dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 14.0 * (1.0 / A.Tm + 1.0 / B.Tm)
		else:
			dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 15.2 * (1.0 / A.Tm + 1.0 / B.Tm)
		
		# 计算杂化贡献
		r_to_p = 0.0
		if A.alpha_beta != "other" and B.alpha_beta != "other":
			if A.alpha_beta != B.alpha_beta:
				r_to_p = self.alpha * A.hybirdvalue * B.hybirdvalue
		
		# 根据过渡金属状态确定p_AB
		if A.isTrans and B.isTrans:
			p_AB = 14.2
		elif A.isTrans or B.isTrans:
			p_AB = 12.35
		else:
			p_AB = 10.7
		
		# 计算化学势差
		df = 2.0 * p_AB * (-(A.phi - B.phi) ** 2 + 9.4 * (A.nws - B.nws) ** 2 - r_to_p) \
		     / (1.0 / A.nws + 1.0 / B.nws)
		
		# 计算ln(Y0)
		lnY0 = 1000.0 * df * B.V * (1.0 + B.u * (B.phi - A.phi)) / (8.314 * Tem) + 1000.0 * dH_trans / (8.314 * Tem)
		
		return lnY0 * (1.0 - entropy_contri_factor)