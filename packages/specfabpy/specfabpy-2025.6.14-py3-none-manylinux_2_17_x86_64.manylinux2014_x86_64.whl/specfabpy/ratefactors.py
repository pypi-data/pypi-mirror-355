#!/usr/bin/python3
# Nicholas M. Rathmann <rathmann@nbi.ku.dk>, 2021-2024

"""
Crystal process rate factors
"""

import numpy as np
import copy, sys, os, code # code.interact(local=locals())
from .specfabpy import specfabpy as sf__ # sf private copy 
lm__, nlm_len__ = sf__.init(20)

"""
Ice
"""

def Gamma0_Lilien23(ugrad, T, tau=None, T0=273.15):
    """
    DDRX rate factor from EDC ice core calibration by Lilien et al. (2023)
    """
#    A = 4.3e7
    A = 1.91e7  
    Q = 3.36e4
    R = 8.314 # gas constant (J/mol*K)
    T += T0
    D = (ugrad + ugrad.T)/2
    epsE = np.sqrt(np.einsum('ij,ji',D,D)/2)
    Gamma0 = epsE * A * np.exp(-Q/(R*T))
    return Gamma0
    
"""
Olivine
"""
