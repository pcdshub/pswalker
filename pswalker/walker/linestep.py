# Proposed walker for Skywalker
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import sympy as sp
from numpy import sqrt
from sympy import tan
from tqdm import tqdm

class LineStep(object):
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

    def align(self):
        # Get M1H X position that puts the beam in the center of the mirror
        mirror_1_x = m1h_x(self.source.x, self.source.xp, self.mirror_1.z)

        # Get M2H X position that puts center of mirror inline with two goal points
        mirror_2_x = m2h_x(self.mirror_2.z, self.imager_1.z, self.imager_2.z,
                           self.goal_x_1, self.goal_x_2)

        # Find alpha 1 that hits center of M2H
        alpha_1 = m1h_alpha(self.source.x, self.source.xp, self.mirror_1.z,
                            self.mirror_2.z, mirror_1_x, mirror_2_x)

        # Find alpha 2 that hits both goal points
        alpha_2 = m2h_alpha(self.source.xp, self.mirror_2.z, self.imager_2.z, alpha_1,
                            mirror_1_x, mirror_2_x, self.goal_x_2)

        return mirror_1_x, mirror_2_x, alpha_1, alpha_2

    def _get_d(self, imager, pos_pix_inp):
        pos_pix_cur = imager.get_centroid()[0]  
        return (pos_pix_cur -pos_pix_inp) * imager.mppix

    @property
    def d1(self):
        return self._get_d(self.imager_1, self.p1)

    @property
    def d2(self):
        return self._get_d(self.imager_2, self.p2) 

    @property
    def goal_x_1(self):
        return self.imager_1.x + (self.p1 - ((
            self.imager_1.image_xsz+1)/2-1))*self.imager_1.mppix

    @property
    def goal_x_2(self):
        return self.imager_2.x + (self.p2 - ((
            self.imager_2.image_xsz+1)/2-1))*self.imager_2.mppix


def m1h_x(x0, xp0, d2):
    return x0 + xp0 * d2

def m2h_x(d4, d5, d6, p1, p2):
    return (d4*p1 - d4*p2 - p1*d6 + d5*p2)/(d5 - d6)

def m1h_alpha(x0, xp0, d2, d4, m1hdx, m2hdx):
    return (d2*xp0 - d4*xp0 + m1hdx - m2hdx)/(2*(d2 - d4))

def m2h_alpha(xp0, d4, d6, a1, m1hdx, m2hdx, p2):
    return (2*a1*d4 - 2*a1*d6 - d4*xp0 + d6*xp0 + m2hdx - p2)/(2*(d4 - d6))


