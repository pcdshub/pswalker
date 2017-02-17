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
        self.tol = kwargs.get("tol", 0.05)   #Tolerance at d1, d2. Tune
        self.max_n = kwargs.get("max_n", 100)   #Max n iterations. Tune

        # Internal
        self._r = self.distance(self.source.pos, self.mirror_1.pos)   #Not sure if this is correct
        self._theta = self.source.xp
        self._l1 = self.distance(self.mirror_1.pos, self.mirror_2.pos)
        self._l2 = self.distance(self.mirror_2.pos, self.imager_1.pos)
        self._l3 = self.distance(self.imager_1.pos, self.imager_2.pos)

        self._n = 0                       #internal counter
        self._turn = "alpha1"             #internal var to determine current turn
        self._d1_x = None
        self._d2_x = None
        
        
    def distance(self, p1, p2):
        return np.linalg.norm(p2-p1)

    def _d1_calc(self):
        """Just in case this needs to be used."""
        return (self._r + self._l1 * (self._theta + self._alpha1) + self._l2 * 
                (self._theta + self._alpha1 + self._alpha2))

    def _d2_calc(self):
        """Just in case this needs to be used."""
        return (self._r + self._l1 * (self._theta + self._alpha1) + (
            self._l2 + self._l3)*(self._theta + self._alpha1 + self._alpha2)

    def _alpha_1_calc(self):
        return ((-self._r - self._theta * (self._l1 + self._l2) - 
                 self.imager_1.alpha * self._l2) / (self._l1 + self._l2))

    def _alpha_2_calc(self):
        return ((-self._r - self._theta * (self._l1 + self._l2 + self._l3) - 
                 self.imager_2.alpha * (self._l1 + self._l2 + self_l3)) / 
                (self._l2 + self._l3))

    def _get_d(self, imager, pos_x_inp):
	    pos_x_cur = imager.get_centroid()[0]   #Double check that this is the correct pos
	    return self.distance(pos_x_inp, pos_x_cur)

	def _step(self):
	    if self._n >= self.max_n:
	        raise StopIteration           #Iterated more than max iters
	    while not (abs(self._d1_x) < self.tol and abs(self._d2_x) < self.tol):
	        if self._turn == "alpha1":
	            self._n += 1
	            yield self._alpha_1_calc()
	            self._turn == "alpha2"
	            self._d2_x = self._get_d(self.imager_2, p2)  
	        elif self._turn == "alpha2":
	            self._n += 1
	            yield self._alpha_2_calc()
	            self._turn == "alpha1"
	            self._d1_x = self._get_d(self.imager_1, p1)
	        else:
	            raise Exception           #How would this ever happen
	    raise StopIteration               #We are within the tolerance

	def step(self, p1=None, p2=None):
		if self.p1 is None or self.p2 is None:
            self.p1 = p1
            self.p2 = p2
		if self._d1_x is None or self._d2_x is None: 
            self._d1_x = self._get_d(self.imager_1, p1)
            self._d2_x = self._get_d(self.imager_2, p2)
        try:
	        return next(self._step), self._turn
        except StopIteration:
	        print("Reached end")
	        return None, None
        
    def align(self, p1=None, p2=None):
        if self.p1 is None or self.p2 is None:
            self.p1 = p1
            self.p2 = p2
        if self._d1_x is None or self._d2_x is None: 
            self._d1_x = self._get_d(self.imager_1, p1)
            self._d2_x = self._get_d(self.imager_2, p2)
        while True:
            try:
                alpha = next(self._step)
                if self._turn == "alpha1"
                    self.imager_1.alpha = alpha
                elif self._turn == "alpha2"
                    self.imager_2.alpha = alpha
            except StopIteration:
                print("Reached end")

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

    
    


