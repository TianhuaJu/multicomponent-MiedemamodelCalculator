import math
import os
from typing import Callable
from scipy.integrate import quad
import BinarySys as Bin_Miedema



def exp(x):
    return math.exp(x)


def _asym_component_choice(k: str, i: str, j: str, phase_state: str, order_degree: str):
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
    bij = Bin_Miedema.Binary(i,j,phase_state= phase_state,order_degree=order_degree)
    bik = Bin_Miedema.Binary(i,k,phase_state= phase_state,order_degree=order_degree)
    bjk = Bin_Miedema.Binary(j,k,phase_state= phase_state,order_degree=order_degree)
   
    a = bij.getEnthalpy_byMiedema_Model(0.5,0.5)
    b = bik.getEnthalpy_byMiedema_Model(0.5,0.5)
    c = bjk.getEnthalpy_byMiedema_Model(0.5,0.5)
    
    # Apply selection rule
    if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
        if (a * b * c > 0):
            t = min(a, b)
            t2 = min(t, c)
            if t2 == a:
                return j
            if t2 == b:
                return i
            else:
                return k
        else:
            t = max(a, b)
            t2 = max(t, c)
            if t2 == a:
                return j
            if t2 == b:
                return i
            else:
                return k
    else:
        t = c if a * b > 0 else b if a * c > 0 else a
        if t == a:
            return j
        if t == b:
            return i
        else:
            return k


def _beta_kj(k: str, j: str, i: str, T: float, phase_state: str, order_degree: str):
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
    bik = Bin_Miedema.Binary(i,k,phase_state= phase_state,order_degree=order_degree)
    bij = Bin_Miedema.Binary(i,j,phase_state= phase_state,order_degree=order_degree)
    bik.set_T(Tem=T)
    bij.set_T(Tem=T)
    def func_yeta(x):
        return (bik.get_excess_Gibbs(x, 1.0 - x) -
                bij.get_excess_Gibbs(x, 1.0 - x))
    
    def func_yeta2(x):
        return func_yeta(x) * func_yeta(x)
    
    # Perform numerical integration
    result = quad(func_yeta2, 0, 1)[0]
    return result


def _df_UEM1(k: str, i: str, T: float, phase_state: str, order_degree: str):
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
    bik = Bin_Miedema.Binary(i,k,phase_state= phase_state,order_degree=order_degree)
    bik.set_T(Tem=T)
    lnYi0 = bik.d_fun10()
    lnYk0 = bik.d_fun20()
    return abs(lnYk0 - lnYi0)


def UEM2_N(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
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
    # Define integration functions for average excess Gibbs energy
    bij = Bin_Miedema.Binary(i,j,phase_state= phase_state,order_degree=order_degree)
    bkj = Bin_Miedema.Binary(k,j,phase_state= phase_state,order_degree=order_degree)
    bij.set_T(Tem=T)
    bkj.set_T(Tem=T)
    bji = Bin_Miedema.Binary(j,i,phase_state= phase_state,order_degree=order_degree)
    bki = Bin_Miedema.Binary(k,i,phase_state= phase_state,order_degree=order_degree)
    bji.set_T(Tem=T)
    bki.set_T(Tem=T)
    def wij(x):
        return bij.get_excess_Gibbs( x, 1-x)
    
    def wkj(x):
        return bkj.get_excess_Gibbs(x, 1-x)
    def wji(x):
        return bji.get_excess_Gibbs(x, 1-x)
    def wki(x):
        return bki.get_excess_Gibbs(x, 1-x)
    Wkj = quad(wkj, 0, 1)[0]
    Wji = quad(wji, 0, 1)[0]
    Wki = quad(wki, 0, 1)[0]
    Wij = quad(wji, 0, 1)[0]
    
    df_kj = abs((Wki - Wji)/(Wki + Wji))
    df_ki = abs((Wkj - Wij)/(Wkj + Wij))
    
    return df_kj/(df_kj + df_ki)*exp(-df_ki)

def Kohler(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
    return 0
def Muggianu(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
    return 0.5
def UEM1(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
    d_ki = _df_UEM1(k, i, T, phase_state, order_degree)
    d_kj = _df_UEM1(k, j, T, phase_state, order_degree)
    
    # Avoid division by zero
    denominator = d_kj + d_ki
    if abs(denominator) < 1e-10:
        return 0.5
    
    contri_coef_ki = d_kj / denominator * exp(-d_ki)
    return contri_coef_ki


def GSM(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
    beta_kj = _beta_kj(k, j, i, T, phase_state, order_degree)
    beta_ki = _beta_kj(k, i, j, T, phase_state, order_degree)
    
    # Avoid division by zero
    denominator = beta_ki + beta_kj
    if abs(denominator) < 1e-10:
        return 0.5
    
    return beta_kj / denominator
def Toop_Kohler(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str):
    asym = _asym_component_choice(k, i, j, phase_state, order_degree)
    
    if asym == k:
        return 0.0
    if asym == i:
        return 0.0
    if asym == j:
        return 1.0
   
# 定义一个函数类型：接受6个特定类型参数并返回float
extrap_func = Callable[[str, str, str, float, str, str], float]

def _get_subBinary_composition(comp_dict: dict, T: float, phase_state: str, order_degree: str, model_func:extrap_func,GeoModel='UEM1'):
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
            b_AB = Bin_Miedema.Binary(A, B,phase_state=phase_state, order_degree=order_degree)
            
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


def get_mixingEnthalpy_byMiedema(comp_dict: dict, T: float, phase_state: str, order_degree: str, model_func:extrap_func,GeoModel='UEM1'):
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
    BinaryList: list[Bin_Miedema.Binary] =  _get_subBinary_composition(comp_dict, T, phase_state, order_degree, model_func,GeoModel)
    
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


def get_excess_Gibbs_byMiedema(comp_dict: dict, T: float, phase_state: str, order_degree: str,model_func:extrap_func,GeoModel='UEM1'):
    '''Calculate excess Gibbs free energy of multi-component system using Miedema model with extrapolation
    
    Args:
        comp_dict (dict): Dictionary of element compositions {element_symbol: mole_fraction}
        T (float): Temperature in K
        phase_state (str): Phase state, 'L' for liquid or 'S' for solid
        order_degree (str): Degree of ordering
      
    
    Returns:
        float: Excess Gibbs free energy in kJ/mol
    '''
    # Calculate sub-binary compositions
    BinaryList: list[Bin_Miedema.Binary] = _get_subBinary_composition(comp_dict, T, phase_state, order_degree, model_func= model_func,GeoModel= GeoModel)
    
    # Calculate total excess Gibbs energy
    gE = 0
    
    if len(BinaryList) >= 1:
        for bij in BinaryList:
            Xi = bij.xA
            Xj = bij.xB
            i, j = bij.A.symbol, bij.B.symbol
            xi, xj = comp_dict[i], comp_dict[j]
            bij.set_T(T)
            # Calculate binary contribution to total excess Gibbs energy
            g_e = 0
            binary_gibbs = bij.get_excess_Gibbs( Xi, Xj)
            if Xi > 0.0 and Xj > 0.0:
                gE += xi * xj / (Xi * Xj) * binary_gibbs
            
    
    return gE


def print_Contri_Coefficient(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str, model_func:extrap_func,GeoModel='UEM1'):
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
    Aki = extrap_func(k, i, j, T, phase_state, order_degree, GeoModel)
    Akj = extrap_func(k, j, i, T, phase_state, order_degree, GeoModel)
    Aij = extrap_func(i, j, k, T, phase_state, order_degree, GeoModel)
    Aji = extrap_func(j, i, k, T, phase_state, order_degree, GeoModel)
    Aik = extrap_func(i, k, j, T, phase_state, order_degree, GeoModel)
    Ajk = extrap_func(j, k, i, T, phase_state, order_degree, GeoModel)
    
    # Create directory if not exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dir1 = os.path.join(current_dir, "contribution_Coefficient", "Miedema-model")
    os.makedirs(dir1, exist_ok=True)
    
    # Determine file name based on model
    if GeoModel == "UEM2":
        file_name = os.path.join(dir1, "UEM2_Normal.txt")
    elif GeoModel == "UEM1":
        file_name = os.path.join(dir1, "UEM1.txt")
    elif GeoModel.lower() in ["chou", "gsm"]:
        file_name = os.path.join(dir1, "GSM相似系数.txt")
    elif GeoModel == "T-K":
        file_name = os.path.join(dir1, "传统外推模型(T-K)贡献系数.txt")
    elif GeoModel == "T-M":
        file_name = os.path.join(dir1, "传统外推模型(T-M)贡献系数.txt")
    else:
        file_name = os.path.join(dir1, f"{GeoModel}_coefficients.txt")
    
    # Write coefficients to file
    with open(file_name, 'a', encoding='utf-8') as f:
        f.write(f'{k}-{i}:\t{Aki},\t{k}-{j}:\t{Akj}\tin\t{i}-{j}\n')
        f.write(f'{i}-{k}:\t{Aik},\t{i}-{j}:\t{Aij}\tin\t{i}-{j}\n')
        f.write(f'{j}-{i}:\t{Aji},\t{j}-{k}:\t{Ajk}\tin\t{i}-{j}\n')
