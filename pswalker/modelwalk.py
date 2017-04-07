# ModelWalker component of CNC

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

class ModelWalker(object):
    """
    Walker component that returns mirror angles using an internal model rather 
    than iterating to get the final position.
    """
    
    def __init__(self, walker, model, **kwargs):
        # Mandatory
        self.walker = walker
        self.model = model
        
        # Optional
        self.do_move = kwargs.get("do_move", False)

    def _calc_alpha_1(self):
        """
        Calculates alpha 1 by passing model values into alpha 1 calc function.
        """
        self.new_alpha_1 = _calc_alpha_1(
            self.model.source.x, self.model.source.xp, self.model.mirror_1.z, 
            self.model.mirror_2.z, self.model.imager_1.z, self.model.imager_2.z,
            self.model.mirror_1.x, self.model.mirror_2.x, self.model.goal_x_1, 
            self.model.goal_x_2)
        return self.new_alpha_1
            
    def _calc_alpha_2(self):
        """
        Calculates alpha 2 by passing model values into alpha 2 calc function.
        """
        self.new_alpha_2 = _calc_alpha_2(
            self.model.source.x, self.model.source.xp, self.new_alpha_1, 
            self.model.mirror_1.z, self.model.mirror_2.z, self.model.imager_2.z,
            self.model.mirror_1.x, self.model.mirror_2.x, self.model.goal_x_2)
        return self.new_alpha_2

    def _move_mirrors(self):
        """
        Tells the walker to move to the designated new alphas.
        """
        self.walker.move_alpha_1(self.new_alpha_1)
        self.walker.move_alpha_2(self.new_alpha_2)

    def step(self, **kwargs):
        """
        Finds the correct angles to move the mirror to then returns them. Will
        also move the mirrors if do_move is True.
        """
        self._calc_alpha_1()
        self._calc_alpha_2()

        if self.do_move:
            self._move_mirrors()
        return self.new_alpha_1, self.new_alpha_2

def _calc_alpha_1(x0, xp0, d2, d4, d5, d6, m1hdx, m2hdx, p1x, p2x):
    """
    Calculates alpha 1 using the inputted values.
    """
    return ((-d4*d5*xp0 + d4*d6*xp0 - d4*p2x + d4*p1x + 2*d5*m1hdx - 2*d5*m2hdx - 
             d5*x0 + d5*p2x - 2*d6*m1hdx + 2*d6*m2hdx + d6*x0 - d6*p1x) / 
            (2*(d2*d5 - d2*d6 - d4*d5 + d4*d6)))

def _calc_alpha_2(x0, xp0, a1, d2, d4, d6, m1hdx, m2hdx, p2x):
    """
    Calculates alpha 2 using the inputted values.
    """
    return (a1*d2 - a1*d6 + d6*xp0/2 - m1hdx + m2hdx - p2x/2 + x0/2)/(d4 - d6)

