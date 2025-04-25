import itertools
import math
import os
from typing import Callable
from scipy.integrate import quad
from sympy import *

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
    # Define integration functions for average Gibbs energy
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


def get_Gibbs_byMiedema(comp_dict: dict, T: float, phase_state: str, order_degree: str,model_func:extrap_func,GeoModel='UEM1'):
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
            # Calculate binary contribution to total Gibbs energy
            
            binary_gibbs = bij.get_excess_Gibbs( Xi, Xj)
            if Xi > 0.0 and Xj > 0.0:
                gE += xi * xj / (Xi * Xj) * binary_gibbs
    entropy_ideal = -8.314*sum([comp_dict[i] *math.log(comp_dict[i])/1000 for i in comp_dict  if comp_dict[i] > 0])
    gibbs_free_energy: float = gE - T*entropy_ideal
    return gibbs_free_energy


def _gmE (Tem: float,phase_state:str, order_degree:str, model_func:extrap_func, GeoModel: str, *args: tuple[str, float]):
    '''摩尔吉布斯自由能函数'''
    comp_dict = dict()
    for kvp in args:
        comp_dict.update({kvp[0]: kvp[1]})
    return get_Gibbs_byMiedema(comp_dict, T=Tem, phase_state =phase_state,order_degree = order_degree, model_func=model_func, GeoModel=GeoModel)

#计算活度系数
def activityCoefficient_calc (comp_dict: dict, solutei: str, solvent: str, Tem: float,phase_state:str, order_degree:str,
                              model_func:extrap_func, GeoModel='UEM1'):
    '''计算活度系数,lnyi
	@param composition: 熔体组成
	@param solutei:待求活度系数的组分i
	@param solvent:人为选定的基体
	@param Tem: 温度 K
	@param geomodel:外推模型
	@param GeoModel: 外推模型代号'''
    
    Gi = 0.0
    Lst = list(comp_dict.keys())
    
    if solutei in Lst and solvent in Lst:
        Lst.remove(solutei)
        Lst.remove(solvent)
    n = len(Lst)
    if n == 0:
        '''一元函数'''
        
        func = lambda x: _gmE(Tem, phase_state,order_degree, model_func,GeoModel, (solutei, x), (solvent, 1 - x))
        GmE = func(comp_dict[solutei])
        x = symbols('x')
        Gmex = func(x)
        
        dg_Ex = diff(Gmex, x, 1).subs({x: comp_dict[solutei]})
        dg_Ex_float = float(dg_Ex.evalf())
        Gi = GmE + dg_Ex_float - comp_dict[solutei] * dg_Ex_float
    if n == 1:
        '''二元函数'''
        xi = comp_dict[solutei]
        xj = comp_dict[Lst[0]]
        
        func = lambda x, x0: _gmE(Tem, phase_state,order_degree, model_func,GeoModel, (solutei, x), (Lst[0], x0), (solvent, 1 - x - x0))
        gmE = func(xi, xj)
        x, x0 = symbols('x,x0')
        gmEx = func(x, x0)
        
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: comp_dict[Lst[0]]})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: comp_dict[Lst[0]]})
        
        Gi = gmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1
    if n == 2:
        '''三元函数'''
        xi = comp_dict[solutei]
        xj = comp_dict[Lst[0]]
        xk = comp_dict[Lst[1]]
        func = lambda x, x0, x1: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0), (Lst[1], x1),
                                      (solvent, 1 - x - x0 - x1))
        x, x0, x1 = symbols('x,x0,x1')
        gmE = func(x=xi, x0=xj, x1=xk)
        gmEx = func(x, x0, x1)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk})
        Gi = gmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2
    if n == 3:
        '''四元函数'''
        xi, xj, xk, xm = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[Lst[2]]
        func = lambda x, x0, x1, x2: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0), (Lst[1], x1),
                                          (Lst[2], x2), (solvent, 1.0 - x - x0 - x1 - x2))
        GmE = func(xi, xj, xk, xm)
        x, x0, x1, x2 = symbols('x,x0,x1,x2')
        gmEx = func(x, x0, x1, x2)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk, x2: xm})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk, x2: xm})
        d_gmEx3 = diff(gmEx, x2, 1).subs({x: xi, x0: xj, x1: xk, x2: xm})
        Gi = GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3
    if n == 4:
        '''五元函数'''
        xi, xj, xk, xm, xn = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[Lst[2]], comp_dict[
            Lst[3]]
        func = lambda x, x0, x1, x2, x3: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0), (Lst[1], x1),
                                              (Lst[2], x2), (Lst[3], x3),
                                              (solvent, 1 - x - x0 - x1 - x2 - x3))
        GmE = func(xi, xj, xk, xm, xn)
        x, x0, x1, x2, x3 = symbols('x,x0,x1,x2,x3')
        gmEx = func(x, x0, x1, x2, x3)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn})
        d_gmEx3 = diff(gmEx, x2, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn})
        d_gmEx4 = diff(gmEx, x3, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn})
        Gi = GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3 - xn * d_gmEx4
    if n == 5:
        '''六元函数'''
        xi, xj, xk, xm, xn, xp = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[Lst[2]], comp_dict[
            Lst[3]], comp_dict[Lst[4]]
        func = lambda x, x0, x1, x2, x3, x4: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0), (Lst[1], x1),
                                                  (Lst[2], x2), (Lst[3], x3), (Lst[4], x4),
                                                  (solvent, 1 - x - x0 - x1 - x2 - x3 - x4))
        x, x0, x1, x2, x3, x4 = symbols('x,x0,x1,x2,x3,x4')
        GmE = func(xi, xj, xk, xm, xn, xp)
        gmEx = func(x, x0, x1, x2, x3, x4)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp})
        d_gmEx3 = diff(gmEx, x2, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp})
        d_gmEx4 = diff(gmEx, x3, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp})
        d_gmEx5 = diff(gmEx, x4, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp})
        Gi = GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3 - xn * d_gmEx4 - xp * d_gmEx5
        pass
    if n == 6:
        '''七元函数'''
        xi, xj, xk, xm, xn, xp, xq = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[Lst[2]], \
        comp_dict[Lst[3]], comp_dict[Lst[4]], comp_dict[Lst[5]]
        func = lambda x, x0, x1, x2, x3, x4, x5: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0), (Lst[1], x1),
                                                      (Lst[2], x2), (Lst[3], x3), (Lst[4], x4), (Lst[5], x5),
                                                      (solvent, 1 - x - x0 - x1 - x2 - x3 - x4 - x5))
        x, x0, x1, x2, x3, x4, x5 = symbols('x,x0,x1,x2,x3,x4,x5')
        GmE = func(xi, xj, xk, xm, xn, xp, xq)
        gmEx = func(x, x0, x1, x2, x3, x4, x5)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        d_gmEx3 = diff(gmEx, x2, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        d_gmEx4 = diff(gmEx, x3, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        d_gmEx5 = diff(gmEx, x4, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        d_gmEx6 = diff(gmEx, x5, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq})
        Gi = (GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3 - xn * d_gmEx4
              - xp * d_gmEx5 - xq * d_gmEx6)
        
        pass
    if n == 7:
        '''八元函数'''
        xi, xj, xk, xm, xn, xp, xq, xr = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[Lst[2]], \
        comp_dict[Lst[3]], comp_dict[Lst[4]], comp_dict[Lst[5]], comp_dict[Lst[6]]
        func = lambda x, x0, x1, x2, x3, x4, x5, x6: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0),
                                                          (Lst[1], x1),
                                                          (Lst[2], x2), (Lst[3], x3), (Lst[4], x4), (Lst[5], x5),
                                                          (Lst[6], x6),
                                                          (solvent, 1 - x - x0 - x1 - x2 - x3 - x4 - x5 - x6))
        x, x0, x1, x2, x3, x4, x5, x6 = symbols('x,x0,x1,x2,x3,x4,x5,x6')
        GmE = func(xi, xj, xk, xm, xn, xp, xq, xr)
        gmEx = func(x, x0, x1, x2, x3, x4, x5, x6)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx3 = diff(gmEx, x2, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx4 = diff(gmEx, x3, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx5 = diff(gmEx, x4, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx6 = diff(gmEx, x5, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        d_gmEx7 = diff(gmEx, x6, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr})
        Gi = (GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3 - xn * d_gmEx4
              - xp * d_gmEx5 - xq * d_gmEx6 - xr * d_gmEx7)
        pass
    if n == 8:
        '''九元函数'''
        xi, xj, xk, xm, xn, xp, xq, xr, xs = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[
            Lst[2]], comp_dict[Lst[3]], comp_dict[Lst[4]], comp_dict[Lst[5]], comp_dict[Lst[6]], comp_dict[Lst[7]]
        func = lambda x, x0, x1, x2, x3, x4, x5, x6, x7: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0),
                                                              (Lst[1], x1),
                                                              (Lst[2], x2), (Lst[3], x3), (Lst[4], x4), (Lst[5], x5),
                                                              (Lst[6], x6), (Lst[7], x7),
                                                              (solvent, 1 - x - x0 - x1 - x2 - x3 - x4 - x5 - x6 - x7))
        x, x0, x1, x2, x3, x4, x5, x6, x7 = symbols('x,x0,x1,x2,x3,x4,x5,x6,x7')
        GmE = func(xi, xj, xk, xm, xn, xp, xq, xr, xs)
        gmEx = func(x, x0, x1, x2, x3, x4, x5, x6, x7)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx1 = diff(gmEx, x0, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx2 = diff(gmEx, x1, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx3 = diff(gmEx, x2, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx4 = diff(gmEx, x3, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx5 = diff(gmEx, x4, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx6 = diff(gmEx, x5, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx7 = diff(gmEx, x6, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        d_gmEx8 = diff(gmEx, x7, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs})
        Gi = (GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3 - xn * d_gmEx4
              - xp * d_gmEx5 - xq * d_gmEx6 - xr * d_gmEx7 - xs * d_gmEx8)
        pass
    if n == 9:
        '''十元函数'''
        xi, xj, xk, xm, xn, xp, xq, xr, xs, xt = comp_dict[solutei], comp_dict[Lst[0]], comp_dict[Lst[1]], comp_dict[
            Lst[2]], comp_dict[Lst[3]], comp_dict[Lst[4]], comp_dict[Lst[5]], comp_dict[Lst[6]], \
            comp_dict[Lst[7]], comp_dict[Lst[8]]
        func = lambda x, x0, x1, x2, x3, x4, x5, x6, x7, x8: _gmE(Tem, phase_state,order_degree, model_func, GeoModel, (solutei, x), (Lst[0], x0),
                                                                  (Lst[1], x1),
                                                                  (Lst[2], x2), (Lst[3], x3), (Lst[4], x4),
                                                                  (Lst[5], x5),
                                                                  (Lst[6], x6), (Lst[7], x7), (Lst[8], x8),
                                                                  (solvent,
                                                                   1 - x - x0 - x1 - x2 - x3 - x4 - x5 - x6 - x7 - x8))
        x, x0, x1, x2, x3, x4, x5, x6, x7, x8 = symbols('x,x0,x1,x2,x3,x4,x5,x6,x7,x8')
        GmE = func(xi, xj, xk, xm, xn, xp, xq, xr, xs, xt)
        gmEx = func(x, x0, x1, x2, x3, x4, x5, x6, x7, x8)
        d_gmEx0 = diff(gmEx, x, 1).subs({x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx1 = diff(gmEx, x0, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx2 = diff(gmEx, x1, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx3 = diff(gmEx, x2, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx4 = diff(gmEx, x3, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx5 = diff(gmEx, x4, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx6 = diff(gmEx, x5, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx7 = diff(gmEx, x6, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx8 = diff(gmEx, x7, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        d_gmEx9 = diff(gmEx, x8, 1).subs(
                {x: xi, x0: xj, x1: xk, x2: xm, x3: xn, x4: xp, x5: xq, x6: xr, x7: xs, x8: xt})
        Gi = (GmE + d_gmEx0 - xi * d_gmEx0 - xj * d_gmEx1 - xk * d_gmEx2 - xm * d_gmEx3 - xn * d_gmEx4
              - xp * d_gmEx5 - xq * d_gmEx6 - xr * d_gmEx7 - xs * d_gmEx8 - xt * d_gmEx9)
        pass
    else:
        pass
    
    return Gi / (8.314 * Tem)


def activityCoefficient_calc_numerical (comp_dict: dict, solutei: str, solvent: str, Tem: float, phase_state: str,
                                        order_degree: str, model_func: extrap_func, GeoModel='UEM1'):
    """使用数值方法计算活度系数，避免符号计算"""
    
    # 获取原始组成
    original_comp = comp_dict.copy()
    xi = original_comp[solutei]
    
    # 定义一个小的增量用于数值微分
    delta = 0.0001
    
    # 计算原始过剩Gibbs能
    GmE_orig = _gmE(Tem, phase_state, order_degree, model_func, GeoModel,
                    *[(k, v) for k, v in original_comp.items()])
    
    # 通过数值方法计算偏导数
    derivatives = {}
    for element in comp_dict:
        if element == solvent:
            continue  # 跳过溶剂元素
        
        # 创建修改后的组成
        modified_comp = original_comp.copy()
        modified_comp[element] += delta
        modified_comp[solvent] -= delta  # 保持总和为1
        
        # 计算修改后的过剩Gibbs能
        GmE_mod = _gmE(Tem, phase_state, order_degree, model_func, GeoModel,
                       *[(k, v) for k, v in modified_comp.items()])
        
        # 计算偏导数
        derivatives[element] = (GmE_mod - GmE_orig) / delta
    
    # 计算活度系数
    Gi = GmE_orig
    for element, deriv in derivatives.items():
        Gi += (1 if element == solutei else 0) * deriv - comp_dict[element] * deriv
    
    return Gi / (8.314 * Tem)


#活度计算
def activity_calc(comp_dict:dict,solutei:str,solvent:str,Tem:float,phase_state:str, order_degree:str, model_func:extrap_func,GeoModel='UEM1'):
	'''
	活度计算，组分i的活度
	@param Tem:温度
	'''
	lnyi = activityCoefficient_calc(comp_dict, solutei, solvent, Tem, phase_state,order_degree, model_func, GeoModel)
	xi = comp_dict[solutei]
	return xi*math.exp(lnyi)

def activity_calc_numerical(comp_dict:dict,solutei:str,solvent:str,Tem:float,phase_state:str, order_degree:str, model_func:extrap_func,GeoModel='UEM1'):
	'''
	活度计算，组分i的活度
	@param Tem:温度
	'''
	lnyi = activityCoefficient_calc_numerical(comp_dict, solutei, solvent, Tem, phase_state,order_degree, model_func, GeoModel)
	xi = comp_dict[solutei]
	return xi*math.exp(lnyi)

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
def _print_Contri_Coefficient(k: str, i: str, j: str, T: float, phase_state: str, order_degree: str, model_func:extrap_func, Gemodel:list,fileName:str):
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
    Aki = format_decimal( model_func(k, i, j, T, phase_state, order_degree))
    Akj = format_decimal( model_func(k, j, i, T, phase_state, order_degree))
    Aij = format_decimal( model_func(i, j, k, T, phase_state, order_degree))
    Aji = format_decimal( model_func(j, i, k, T, phase_state, order_degree))
    Aik = format_decimal( model_func(i, k, j, T, phase_state, order_degree))
    Ajk = format_decimal( model_func(j, k, i, T, phase_state, order_degree))
    
    
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
                
   
        

def print_Contri_Coeff(compositions: dict, T: float, phase_state: str, order_degree: str, model_func:extrap_func,GeoModel:list):
    keys = list(compositions.keys())
    key_combinations = list(itertools.combinations(keys, 3))
    for key_combination in key_combinations:
        k1, i1, j1 = key_combination
        fileName = f'{k1}-{i1}-{j1}-{T}'
        _print_Contri_Coefficient(k1, i1, j1, T, phase_state, order_degree, model_func, GeoModel,fileName)