# Proposed walker for Skywalker
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from numpy import sqrt

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
        self.p2 = kwargs.get("p2", None)   #Desired point at imager 1
        self.tol = kwargs.get("tol", 1e-7)   #Tolerance at d1, d2. Tune
        self.max_n = kwargs.get("max_n", 200)   #Max n iterations. Tune

        # Internal
        # self._r = self.distance(self.source.pos, self.mirror_1.pos)   #Not sure if this is correct
        self._r = self.source.x 
        self._theta = self.source.xp - np.pi/4
        self._l1 = self.distance(self.mirror_1.pos, self.mirror_2.pos)
        self._l2 = self.distance(self.mirror_2.pos, self.imager_1.pos)
        self._l3 = self.distance(self.imager_1.pos, self.imager_2.pos)

        self._n = 0                       #internal counter
        self._turn = "alpha1"             #internal var to determine current turn
        self._d1_x = None
        self._d2_x = None
        
        
    def distance(self, p1, p2):
        if not isinstance(p1, np.ndarray):
            p1 = np.array(p1)
        if not isinstance(p2, np.ndarray):
            p2 = np.array(p2)


        return np.linalg.norm(p2-p1)

    def _d1_calc(self):
        """Just in case this needs to be used."""
        return (self._r + self._l1 * (self._theta + self.mirror_1.alpha) + self._l2 * 
                (self._theta + self.mirror_1.alpha + self.mirror_2.alpha))

    def _d2_calc(self):
        """Just in case this needs to be used."""
        return (self._r + self._l1 * (self._theta + self.mirror_1.alpha) + (
            self._l2 + self._l3)*(self._theta + self.mirror_1.alpha + self.mirror_2.alpha))

    def _alpha_1_calc(self):
        return ((-self._r - self._theta * (self._l1 + self._l2) - 
                 self.mirror_2.alpha * self._l2) / (self._l1 + self._l2))

    def _alpha_2_calc(self):
        return -((-self._r - self._theta * (self._l1 + self._l2 + self._l3) - 
                 self.mirror_1.alpha * (self._l1 + self._l2 + self._l3)) / 
                (self._l2 + self._l3))

    def _alpha_1_calc_2(self):
        return alpha1(self.source.x, self.source.xp, self.mirror_2.alpha, 
                      self.mirror_1.z, self.mirror_2.z, self.imager_1.z,
                      self.mirror_1.x, self.mirror_2.x, 
                      self.imager_1.x + (self.p1-600) * self.imager_1.mppix)

    def _alpha_2_calc_2(self):
        return alpha1(self.source.x, self.source.xp, self.mirror_1.alpha, 
                      self.mirror_1.z, self.mirror_2.z, self.imager_2.z,
                      self.mirror_1.x, self.mirror_2.x,
                      self.imager_2.x + (self.p2-600) * self.imager_2.mppix)

    def _get_d(self, imager, pos_pix_inp):
        pos_pix_cur = imager.get_centroid()[0]   #Double check that this is the correct pos
        return (pos_pix_cur -pos_pix_inp) * imager.mppix

    def _move_mirror(self, alpha):
	    if self._turn == "alpha1":
		    self.mirror_1.alpha = alpha
	    elif self._turn == "alpha2":
	        self.mirror_2.alpha = alpha
	    else:
	        raise Exception

    def _step(self):
        if self._n >= self.max_n:
            raise StopIteration("Reached max number of iterations")
        while abs(self._d1_x) > self.tol or abs(self._d2_x) > self.tol:
            self._old_turn = self._turn
            if self._turn == "alpha1":
                self._n += 1
                self._turn = "alpha2"
                self._d2_x = self._get_d(self.imager_2, self.p2)
                yield self._alpha_1_calc()
            elif self._turn == "alpha2":
                self._n += 1
                self._turn = "alpha1"
                self._d1_x = self._get_d(self.imager_1, self.p1)
                yield self._alpha_2_calc()
            else:
                raise Exception           #How would this ever happen
        raise StopIteration("D1 and D2 within tolerance")

    def step(self, p1=None, p2=None, do_step=False):

        # import ipdb; ipdb.set_trace()

        if p1 is not None: self.p1 = p1
        if p2 is not None: self.p2 = p2
        # if self._d1_x is None or self._d2_x is None: 
        self._d1_x = self._get_d(self.imager_1, self.p1)
        self._d2_x = self._get_d(self.imager_2, self.p2)

        # import ipdb; ipdb.set_trace()

        next_alpha = next(self._step())

        # print(self._d1_calc(), self._d2_calc())

        if do_step:
            self._move_mirror(next_alpha)
        else:
            return next_alpha, self._old_turn
        
    def align(self, p1=None, p2=None):
        if p1: self.p1 = p1
        if p2: self.p2 = p2
        if self._d1_x is None or self._d2_x is None: 
            self._d1_x = self._get_d(self.imager_1, self.p1)
            self._d2_x = self._get_d(self.imager_2, self.p2)
        while True:
            try:
                alpha = next(self._step())
                self._move_mirror(alpha)
            except StopIteration:
                print("Reached end")


def alpha1(x0, xp0, a2, d2, d4, d5, m1hdx, m2hdx, x):
	return (-a2*d2 + 4*a2*d4 - 3*a2*d5 + 2*d4*xp0 - 2*d5*xp0 - m2hdx + x - sqrt(a2**2*d2**2 - 8*a2**2*d2*d4 + 6*a2**2*d2*d5 + 8*a2**2*d4**2 - 8*a2**2*d4*d5 + a2**2*d5**2 - 4*a2*d2*d4*xp0 + 4*a2*d2*d5*xp0 + 2*a2*d2*m2hdx - 2*a2*d2*x + 8*a2*d4*m1hdx - 8*a2*d4*m2hdx + 4*a2*d4*x - 4*a2*d4*x0 - 8*a2*d5*m1hdx + 6*a2*d5*m2hdx - 2*a2*d5*x + 4*a2*d5*x0 + m2hdx**2 - 2*m2hdx*x + x**2))/(4*(d4 - d5))
            

def alpha2(x0, xp0, a1, d2, d4, d6, m1hdx, m2hdx, x):
	return (-2*a1*d2 + 8*a1*d4 - 6*a1*d6 - 4*d4*xp0 + 3*d6*xp0 + 2*m1hdx - x - x0 - sqrt(4*a1**2*d2**2 - 32*a1**2*d2*d4 + 24*a1**2*d2*d6 + 32*a1**2*d4**2 - 32*a1**2*d4*d6 + 4*a1**2*d6**2 + 16*a1*d2*d4*xp0 - 12*a1*d2*d6*xp0 - 8*a1*d2*m1hdx + 4*a1*d2*x + 4*a1*d2*x0 - 32*a1*d4**2*xp0 + 32*a1*d4*d6*xp0 + 32*a1*d4*m1hdx - 16*a1*d4*m2hdx - 16*a1*d4*x0 - 4*a1*d6**2*xp0 - 24*a1*d6*m1hdx + 16*a1*d6*m2hdx - 4*a1*d6*x + 12*a1*d6*x0 + 8*d4**2*xp0**2 - 8*d4*d6*xp0**2 - 16*d4*m1hdx*xp0 + 8*d4*m2hdx*xp0 + 8*d4*x0*xp0 + d6**2*xp0**2 + 12*d6*m1hdx*xp0 - 8*d6*m2hdx*xp0 + 2*d6*x*xp0 - 6*d6*x0*xp0 + 4*m1hdx**2 - 4*m1hdx*x - 4*m1hdx*x0 + x**2 + 2*x*x0 + x0**2))/(4*(d4 - d6))


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

    
    


