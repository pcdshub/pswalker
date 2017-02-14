# Proposed walker for Skywalker

import tqdm
import numpy as np
import matplotlib.pyplot as plt
from joblib import Memory

l0 = 1.0
l1 = 11.33
l2 = 1.192
l3 = 271 - l2

d1 = 0
d2 = 0

r = 0.1
theta = 0.1

alpha1 = 0
alpha2 = 0

beam_radius = 5e-4
acceptable_beam_tolerance = 0.05

tolerance = beam_radius * acceptable_beam_tolerance * 0.5

N = 50

def d1_calc(r, theta, l1, l2, alpha1, alpha2):
    return r + l1 * (theta + alpha1) + l2 * (theta + alpha1 + alpha2)

def d2_calc(r, theta, l1, l2, l3, alpha1, alpha2):
    return r + l1*(theta + alpha1) + (l2+l3)*(theta + alpha1 + alpha2)

def alpha1_calc(r, theta, l1, l2, alpha2):
    return (-r - theta*(l1 + l2) - alpha2*l2)/(l1 + l2)

def alpha2_calc(r, theta, l1, l2, l3, alpha1):
    return (-r - theta*(l1 + l2 + l3) - alpha1*(l1 + l2 + l3))/(l2 + l3)

def align(r, theta, l1, l2, l3, alpha1, alpha2):
    d1 = d1_calc(r, theta, l1, l2, alpha1, alpha2)
    d2 = d2_calc(r, theta, l1, l2, l3, alpha1, alpha2)
    n = 0
    print(d1,d2)
    while (abs(d1) > tolerance or abs(d2) > tolerance) and n < N:
        alpha1 = alpha1_calc(r, theta, l1, l2, alpha2)
        d2 = d2_calc(r, theta, l1, l2, l3, alpha1, alpha2)
        alpha2 = alpha2_calc(r, theta, l1, l2, l3, alpha1)
        d1 = d1_calc(r, theta, l1, l2, alpha1, alpha2)
        n+=1
        print("At iteration {0}".format(n))
        print("  Alpha1: {0}, Alpha2: {1}".format(alpha1,alpha2))
        print("  D1 Error: {0}, D2 Error: {1}\n".format(d1,d2))    
            
    print("Number of iterations {0}".format(n))
    print("Final Values:")
    print("  Alpha1: {0}, Alpha2: {1}".format(alpha1,alpha2))
    print("  D1 Error: {0}, D2 Error: {1}".format(d1,d2))

        

align(r, theta, l1, l2, l3, alpha1, alpha2)

    
    


