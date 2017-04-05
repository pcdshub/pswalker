# Proposed walker for Skywalker
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import sympy as sp
from numpy import sqrt
from sympy import tan
from tqdm import tqdm

class IterWalker(object):
    def __init__(self, source, mirror_1, mirror_2, imager_1, imager_2, **kwargs):
        # Required
        self.source = source
        self.mirror_1 = mirror_1
        self.mirror_2 = mirror_2
        self.imager_1 = imager_1
        self.imager_2 = imager_2

        # Optional Args
        self.p1 = kwargs.get("p1", None)   #Desired point at imager 1
        self.p2 = kwargs.get("p2", None)   #Desired point at imager 2
        # self.tol = kwargs.get("tol", 1e-7)   #Tolerance at d1, d2. Tune
        self.tan = kwargs.get("tan", False)
        self.max_n = kwargs.get("max_n", 200)   #Max n iterations. Tune

        # # Internal
        self._alpha_1 = self.mirror_1.alpha
        self._alpha_2 = self.mirror_2.alpha

        # self.goal_x_1 = 
        # self.goal_x_2 =    #Logic should be reversed
        # # import IPython; IPython.embed()
        
        # self.d1 = self._get_d(self.imager_1, self.p1)
        # self.d2 = self._get_d(self.imager_2, self.p2)        
        
    def distance(self, p1, p2):
        if not isinstance(p1, np.ndarray):
            p1 = np.array(p1)
        if not isinstance(p2, np.ndarray):
            p2 = np.array(p2)
        return np.linalg.norm(p2-p1)

    def _alpha_1_calc(self, s=False):
        # self.goal_x_1 = self.imager_1.x - (self.p1 - ((
        #     self.imager_1.image_xsz+1)/2-1))*self.imager_1.mppix
        return alpha1(self.source.x, self.source.xp, self._alpha_2, 
                      self.mirror_1.z, self.mirror_2.z, self.imager_1.z,
                      self.imager_2.z,
                      self.mirror_1.x, self.mirror_2.x, self.goal_x_1, 
                      self.goal_x_2, t=self.tan,
                      s=s)

    def _alpha_2_calc(self):
        # self.goal_x_2 = self.imager_2.x - (self.p2 - ((
        #     self.imager_2.image_xsz+1)/2-1))*self.imager_2.mppix   #Logic should be reversed
        return alpha2(self.source.x, self.source.xp, self._alpha_1, 
                      self.mirror_1.z, self.mirror_2.z, self.imager_2.z,
                      self.mirror_1.x, self.mirror_2.x, self.goal_x_2, t=self.tan)

    def _get_d(self, imager, pos_pix_inp):
        pos_pix_cur = imager.get_centroid()[0]   #Double check that this is the correct pos
        return (pos_pix_cur -pos_pix_inp) * imager.mppix

    def _move_mirrors(self, alpha_1, alpha_2):
        self.mirror_1.alpha = alpha_1
        self.mirror_2.alpha = alpha_2

    def step(self):
        return self._alpha_1_calc(), self._alpha_2_calc()
        
    def align(self, p1=None, p2=None, move=False):
        if p1 is not None: self.p1 = p1
        if p2 is not None: self.p2 = p2
        for i in range(self.max_n):
            self._alpha_1 = self._alpha_1_calc()
            self._alpha_2 = self._alpha_2_calc()
            # import IPython; IPython.embed()
            # print(self._alpha_1, self._alpha_2)
        if move is True:
            self._move_mirrors(self._alpha_1, self._alpha_2)
        return self._alpha_1, self._alpha_2

    def align2(self, p1=None, p2=None, move=False):
        if p1 is not None: self.p1 = p1
        if p2 is not None: self.p2 = p2
        self._alpha_1 = self._alpha_1_calc(s=True)
        self._alpha_2 = self._alpha_2_calc()
        if move is True:
            self._move_mirrors(self._alpha_1, self._alpha_2)
        return self._alpha_1, self._alpha_2
        
    @property
    def d1(self):
        return self._get_d(self.imager_1, self.p1)

    @property
    def d2(self):
        return self._get_d(self.imager_2, self.p2) 

    @property
    def goal_x_1(self):
        goal = self.imager_1.x + (self.p1 - self.imager_1.image_xsz/2 + 1)*self.imager_1.mppix
        # print(goal)
        return goal

    @property
    def goal_x_2(self):
        goal = self.imager_2.x + (self.p2 - self.imager_2.image_xsz/2 + 1)*self.imager_2.mppix
        # import IPython; IPython.embed()
        # print(goal)
        return goal
        
# x0, xp0, a1, a2, d2, d4, d5, d6, m1hdx, m2hdx, x, = sp.symbols(
# 	"x0 xp0 a1 a2 d2 d4 d5 d6 m1hdx m2hdx x")

def alpha1(x0, xp0, a2, d2, d4, d5, d6, m1hdx, m2hdx, p1, p2, t=False, s=False):
    if t is False:        
        return (-d4*d5*xp0 + d4*d6*xp0 - d4*p2 + d4*p1 + 2*d5*m1hdx - 2*d5*m2hdx - d5*x0 + d5*p2 - 2*d6*m1hdx + 2*d6*m2hdx + d6*x0 - d6*p1)/(2*(d2*d5 - d2*d6 - d4*d5 + d4*d6))
    elif s is True:
        return (-d4*xp0/2 + m1hdx - m2hdx + x/2 - x0/2)/(d2 - d4)
    elif t is True:
        a1 = sp.symbols("a1")
        return sp.nsolve(
            (d2*tan(a1)*tan(a2)*tan(xp0) - d2*tan(a1)*tan(a2)*tan(2*a1 - xp0) + 
             d4*tan(a1)*tan(a2)*tan(2*a1 - xp0) - 
            d4*tan(a2)*tan(xp0)*tan(2*a1 - xp0) - m1hdx*tan(a2)*tan(xp0) + 
            m1hdx*tan(a2)*tan(2*a1 - xp0) - m2hdx*tan(a1)*tan(2*a1 - xp0) + 
            m2hdx*tan(xp0)*tan(2*a1 - xp0) + x0*tan(a1)*tan(a2) - 
            x0*tan(a2)*tan(2*a1 - xp0) + (-d4 + d5)*(
                tan(a1)*tan(a2) - tan(a1)*tan(2*a1 - xp0) - tan(a2)*tan(xp0) + 
                tan(xp0)*tan(2*a1 - xp0))*tan(-2*a1 + 2*a2 + xp0)) / 
            (tan(a1)*tan(a2) - tan(a1)*tan(2*a1 - xp0) - tan(a2)*tan(xp0) + 
             tan(xp0)*tan(2*a1 - xp0)) - x, 0.0014)
        
            
def alpha2(x0, xp0, a1, d2, d4, d6, m1hdx, m2hdx, x, t=False):
    if t is False:
        return (a1*d2 - a1*d6 + d6*xp0/2 - m1hdx + m2hdx - x/2 + x0/2)/(d4 - d6)
    elif t is True:
        a2 = sp.symbols("a2")
        return sp.nsolve(
            (d2*tan(a1)*tan(a2)*tan(xp0) - d2*tan(a1)*tan(a2)*tan(2*a1 - xp0) + 
             d4*tan(a1)*tan(a2)*tan(2*a1 - xp0) - 
            d4*tan(a2)*tan(xp0)*tan(2*a1 - xp0) - m1hdx*tan(a2)*tan(xp0) + 
            m1hdx*tan(a2)*tan(2*a1 - xp0) - m2hdx*tan(a1)*tan(2*a1 - xp0) + 
            m2hdx*tan(xp0)*tan(2*a1 - xp0) + x0*tan(a1)*tan(a2) - 
            x0*tan(a2)*tan(2*a1 - xp0) + (-d4 + d6)*(
                tan(a1)*tan(a2) - tan(a1)*tan(2*a1 - xp0) - tan(a2)*tan(xp0) + 
                tan(xp0)*tan(2*a1 - xp0))*tan(-2*a1 + 2*a2 + xp0)) / 
            (tan(a1)*tan(a2) - tan(a1)*tan(2*a1 - xp0) - tan(a2)*tan(xp0) + 
             tan(xp0)*tan(2*a1 - xp0)) - x, 0.0014)


# def align(r, theta, l1, l2, l3, alpha1, alpha2):
#     d1 = d1_calc(r, theta, l1, l2, alpha1, alpha2)
#     d2 = d2_calc(r, theta, l1, l2, l3, alpha1, alpha2)
#     n = 0
#     print(d1,d2)
#     while (abs(d1) > tolerance or abs(d2) > tolerance) and n < N:
#         alpha1 = alpha1_calc(r, theta, l1, l2, alpha2)
#         d2 = d2_calc(r, theta, l1, l2, l3, alpha1, alpha2)
#         alpha2 = alpha2_calc(r, theta, l1, l2, l3, alpha1)
#         d1 = d1_calc(r, theta, l1, l2, alpha1, alpha2)
#         n+=1
#         print("At iteration {0}".format(n))
#         print("  Alpha1: {0}, Alpha2: {1}".format(alpha1,alpha2))
#         print("  D1 Error: {0}, D2 Error: {1}\n".format(d1,d2))    
            
#     print("Number of iterations {0}".format(n))
#     print("Final Values:")
#     print("  Alpha1: {0}, Alpha2: {1}".format(alpha1,alpha2))
#     print("  D1 Error: {0}, D2 Error: {1}".format(d1,d2))

        

# align(r, theta, l1, l2, l3, alpha1, alpha2)

    
    


