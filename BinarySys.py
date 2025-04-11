import os
import sqlite3 as sq
import time
class Element:
	'''Element class for storing element properties'''
	
	def __init__ (self, A: str) -> None:
		'''Initialize element class and automatically connect to database to get element properties
		
		Args:
			A (str): Element symbol
		'''
		table = "Miedema1983"
		self._querydata(A, table)
	
	def _querydata (self, A: str, table: str):
		'''Connect to database and retrieve data
		
		Args:
			A (str): Element symbol
			table (str): Database table name
		
		Raises:
			Exception: If database connection or query fails
		'''
		try:
			# Determine the path to the database
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


class Binary:
	'''Binary system class for storing binary system composition from extrapolation model'''
	
	def __init__ (self, A: str, B: str,phase_state: str, order_degree='IM'):
		'''Initialize binary system
		
		Args:
			A (str): First element symbol
			B (str): Second element symbol
		'''
		self.lammda = 0.0
		self.A = Element(A)
		self.B = Element(B)
		self.xA = 0.0
		self.xB = 0.0
		# Set alpha based on phase state
		if phase_state == 'S':
			self.alpha = 1.0
		elif phase_state == 'L':
			self.alpha = 0.73
		else:
			raise ValueError(f"Invalid phase_state: {phase_state}. Must be 'S' or 'L'.")
			# Set lambda based on order degree
		if order_degree == 'SS':
			self.lammda = 0.0
		elif order_degree == 'AMP':
			self.lammda = 5.0
		elif order_degree == 'IM':
			self.lammda = 8.0
		else:
			raise ValueError(f"Invalid order_degree: {order_degree}. Must be 'SS', 'AMP', or 'IM'.")
	
	def set_X (self, xA: float, xB: float):
		'''Set composition of binary system
		
		Args:
			xA (float): Mole fraction of element A
			xB (float): Mole fraction of element B
		'''
		total = xA + xB
		self.xA = xA / total
		self.xB = xB / total
		
	def set_T (self, Tem:float):
		self.Tem = Tem


	def _V_in_alloy (self,  xA:float, xB:float):
		'''Calculate volume of elements in alloy
		
		Args:
			
			xA (float): Mole fraction of element A
			xB (float): Mole fraction of element B
			
		Returns:
			tuple: (Volume of element A in alloy, Volume of element B in alloy)
		'''
		
		max_time = 10.0
		A = self.A
		B = self.B
		
		
		V1a, V2a = A.V, B.V
		
		start_time = time.time()
		
		# Maximum number of iterations to prevent infinite loop
		max_iterations = 1000
		iterations = 0
		
		# Convergence criteria
		epsilon = 1e-6
		
		while iterations < max_iterations:
			V1_tem, V2_tem = V1a, V2a
			
			# Calculate molar volume fractions
			Pax = xA * V1_tem / (xB * V2_tem + xA * V1_tem)
			Pbx = xB * V2_tem / (xB * V2_tem + xA * V1_tem)
			
			# Update volumes
			V1a = A.V * (1.0 + A.u * Pbx * (1.0 + self.lammda * pow(Pax * Pbx, 2.0)) * (A.phi - B.phi))
			V2a = B.V * (1.0 + B.u * Pax * (1.0 + self.lammda * pow(Pax * Pbx, 2.0)) * (B.phi - A.phi))
			
			# Check convergence
			if abs(V1a - V1_tem) < epsilon and abs(V2a - V2_tem) < epsilon:
				break
			
			# Check if time limit exceeded
			if time.time() - start_time > max_time:
				print(f"Warning: Volume calculation did not converge within {max_time} seconds.")
				break
			
			iterations += 1
		
		# Check if max iterations reached
		if iterations == max_iterations:
			print("Warning: Volume calculation did not converge within maximum iterations.")
		
		return V1a, V2a


	def getEnthalpy_byMiedema_Model (self,xA: float, xB: float):
		'''Calculate enthalpy of formation using Miedema model
		
		Args:
			
			xA (float): Mole fraction of element A
			xB (float): Mole fraction of element B
			
		Returns:
			float: Enthalpy of formation in kJ/mol
		'''
		
		# Initialize elements
		try:
			element_A = self.A
			element_B = self.B
		except Exception as e:
			raise Exception(f"Error initializing elements: {str(e)}")
		
		
		# Normalize mole fractions
		total = xA + xB
		x1 = xA / total
		x2 = xB / total
		
		# Calculate r_to_p (hybridization contribution)
		r_to_p = 0.0
		if element_A.alpha_beta != "other" and element_B.alpha_beta != "other":
			if element_A.alpha_beta != element_B.alpha_beta:
				r_to_p = self.alpha * element_A.hybirdvalue * element_B.hybirdvalue
		
		# Determine p_AB based on transition metal status
		if element_A.isTrans and element_B.isTrans:
			p_AB = 14.2
		elif element_A.isTrans or element_B.isTrans:
			p_AB = 12.35
		else:
			p_AB = 10.7
		
		# Calculate chemical potential difference
		df = 2.0 * p_AB * (
				-pow(element_A.phi - element_B.phi, 2.0) + 9.4 * pow(element_A.nws - element_B.nws, 2.0) - r_to_p) \
		     / (1.0 / element_A.nws + 1.0 / element_B.nws)
		
		# Calculate volumes in alloy
		V_Aa, V_Ba = self._V_in_alloy(xA=xA, xB=xB)
		
		# Calculate concentration factors
		cAs = x1 * V_Aa / (x1 * V_Aa + x2 * V_Ba)
		cBs = x2 * V_Ba / (x1 * V_Aa + x2 * V_Ba)
		
		# Calculate interface concentration function
		fC = (cAs * cBs * (1.0 + self.lammda * pow(cAs * cBs, 2.0))) * (x1 * V_Aa + x2 * V_Ba)
		
		# Calculate transformation enthalpy contribution
		dH_trans = x1 * element_A.dHtrans + x2 * element_B.dHtrans
		
		# Calculate total enthalpy
		total_enthalpy = fC * df + dH_trans
		
		return total_enthalpy


	def _get_excess_entropy (self,xA: float, xB: float):
		'''Calculate excess entropy using Tanaka excess entropy relation
		
		Args:
			
			xA (float): Mole fraction of element A
			xB (float): Mole fraction of element B
			
		Returns:
			float: Excess entropy in J/(mol·K)
		'''
		try:
			element_A = self.A
			element_B = self.B
		except Exception as e:
			raise Exception(f"Error initializing elements: {str(e)}")
		
		# Calculate mixing enthalpy
		Hmix = self.getEnthalpy_byMiedema_Model(xA=xA, xB=xB)
		
		# Calculate excess entropy based on phase state
		if self.alpha == 0.73:
			excess_entropy = 1.0 / 14 * (1.0 / element_A.Tm + 1.0 / element_B.Tm) * Hmix
		else:
			excess_entropy = 1.0 / 15.1 * (1.0 / element_A.Tm + 1.0 / element_B.Tm) * Hmix
		
		return excess_entropy


	def get_excess_Gibbs (self,xA:float,xB:float):
		'''Calculate excess Gibbs free energy of binary alloy
		
		Args:
			
			xA (float): Mole fraction of element A
			xB (float): Mole fraction of element B
			
		
		Returns:
			float: Excess Gibbs free energy in kJ/mol
		'''
		# Calculate enthalpy and entropy contributions
		enthalpy = self.getEnthalpy_byMiedema_Model(xA=xA, xB=xB)
		entropy = self._get_excess_entropy(xA=xA, xB=xB)
		
		# Calculate excess Gibbs free energy
		g_E = enthalpy - self.Tem * entropy
		
		return g_E
	def d_fun10(self):
		'''Calculate partial molar excess Gibbs free energy of A
		 in A-B binary alloy at temperature Tem under dilution
		 lnγ_A
		 '''
		A = self.A
		B = self.B
		Tem = self.Tem
		# Special elements list
		special_element = ["Si", "Ge", "C", "P"]
		
		# Set parameters based on phase state
		dH_trans = 0.0
		entropy_contri_factor = 0.0
		
		if self.alpha == 0.73:
			if self.A.symbol in special_element:
				dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 14.0 * (1.0 / A.Tm + 1.0 / B.Tm)
		else:
			dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 15.2 * (1.0 / A.Tm + 1.0 / B.Tm)
		
		
		
		# Calculate hybridization contribution
		r_to_p = 0.0
		if A.alpha_beta != "other" and B.alpha_beta != "other":
			if A.alpha_beta != B.alpha_beta:
				r_to_p = self.alpha * A.hybirdvalue * B.hybirdvalue
		
		# Determine p_AB based on transition metal status
		if A.isTrans and B.isTrans:
			p_AB = 14.2
		elif A.isTrans or B.isTrans:
			p_AB = 12.35
		else:
			p_AB = 10.7
		
		# Calculate chemical potential difference
		df = 2.0 * p_AB * (-pow(A.phi - B.phi, 2.0) + 9.4 * pow(A.nws - B.nws, 2.0) - r_to_p) \
		     / (1.0 / A.nws + 1.0 / B.nws)
		
		# Calculate ln(Y0)
		lnY0 = 1000.0 * df * B.V * (1.0 + B.u * (B.phi - A.phi)) / (8.314 * Tem) + 1000.0 * dH_trans / (8.314 * Tem)
		
		return lnY0 * (1.0 - entropy_contri_factor)
	
	def d_fun20 (self):
		'''Calculate partial molar excess Gibbs free energy of B
		 in A-B binary alloy at temperature Tem under dilution
		 lnγ_B
		 '''
		A = self.B
		B = self.A
		Tem = self.Tem
		# Special elements list
		special_element = ["Si", "Ge", "C", "P"]
		
		# Set parameters based on phase state
		dH_trans = 0.0
		entropy_contri_factor = 0.0
		
		if self.alpha == 0.73:
			if self.A.symbol in special_element:
				dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 14.0 * (1.0 / A.Tm + 1.0 / B.Tm)
		else:
			dH_trans = B.dHtrans
			entropy_contri_factor = 1.0 / 15.2 * (1.0 / A.Tm + 1.0 / B.Tm)
		
		# Calculate hybridization contribution
		r_to_p = 0.0
		if A.alpha_beta != "other" and B.alpha_beta != "other":
			if A.alpha_beta != B.alpha_beta:
				r_to_p = self.alpha * A.hybirdvalue * B.hybirdvalue
		
		# Determine p_AB based on transition metal status
		if A.isTrans and B.isTrans:
			p_AB = 14.2
		elif A.isTrans or B.isTrans:
			p_AB = 12.35
		else:
			p_AB = 10.7
		
		# Calculate chemical potential difference
		df = 2.0 * p_AB * (-pow(A.phi - B.phi, 2.0) + 9.4 * pow(A.nws - B.nws, 2.0) - r_to_p) \
		     / (1.0 / A.nws + 1.0 / B.nws)
		
		# Calculate ln(Y0)
		lnY0 = 1000.0 * df * B.V * (1.0 + B.u * (B.phi - A.phi)) / (8.314 * Tem) + 1000.0 * dH_trans / (8.314 * Tem)
		
		return lnY0 * (1.0 - entropy_contri_factor)
