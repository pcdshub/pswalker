################################################################################
#                                  Skywalker                                   #
################################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from psp.Pv import Pv
from joblib import Memory
from beamDetector.detector import Detector
from walker.iterwalk import IterWalker

################################################################################
#                                Imager Class                                  #
################################################################################

class Imager(object):
    """
    Imager object that will encapsulate the various yag screens along the
    beamline.
    """

    def __init__(self, pv_camera, pv_x, pv_z, detector=Detector()):
        self.pv_obj_camera = Pv(pv_camera)
        self.pv_obj_x = Pv(pv_x)
        self.pv_obj_z = Pv(pv_z)
        self.detector = detector
        self.image    = None
        self.centroid = None
        self.bounding_box = None

    def get(self):
        """Get an image from the imager."""
        self.image = Pv.get()
        return self.image

    def get_centroid(self):
        """Return the centroid of the image."""
        self.centroid, self.bounding_box = self.detector.find(Pv.get())
        return self.centroid

    @property
    def x(self):
        return self.pv_obj_x.get()

    @x.setter
    def x(self, val):
        put_val(self.pv_obj_x, val)

    @property
    def z(self):
        return self.pv_obj_z.get()

    @z.setter
    def z(self, val):
        put_val(self.pv_obj_z, val)

    @property
    def pos(self):
        return np.array([self.pv_obj_z.get(), self.pv_obj_x.get()])



################################################################################
#                                Mirror Class                                  #
################################################################################

class Mirror(object):
    """
    Mirror class to encapsulate the two HOMS (or any) mirrors.
    """

    def __init__(self, pv_x, pv_alpha, pv_z):
        self.pv_obj_x = Pv(pv_x)
        self.pv_obj_xp = Pv(pv_xp)
        self.pv_obj_z = Pv(pv_z)

    @property
    def x(self):
        return self.pv_obj_x.get()

    @x.setter
    def x(self, val):
        put_val(self.pv_obj_x, val)
            
    @property
    def alpha(self):
        return self.pv_obj_alpha.get()

    @alpha.setter
    def alpha(self, val):
        put_val(self.pv_obj_alpha, val)

    @property
    def z(self):
        return self.pv_obj_z.get()

    @z.setter
    def z(self, val):
        put_val(self.pv_obj_z, val)

    @property
    def pos(self):
        return np.array([self.pv_obj_z.get(), self.pv_obj_x.get()])


                

################################################################################
#                                Source Class                                  #
################################################################################

class Source(object):
    def __init__(self, pv_x, pv_xp, pv_y, pv_yp, pv_z):
        self.pv_obj_x  = Pv(pv_x)
        self.pv_obj_xp = Pv(pv_xp)
        self.pv_obj_y  = Pv(pv_y)
        self.pv_obj_yp = Pv(pv_yp)
        self.pv_obj_z = Pv(pv_z)

    def put_val(self, pv, val):
        try:
            pv.put(float(val))
        except ValueError:
            print("Invalid input type. Must be castable to float.")
    
    @property
    def x(self):
        return self.pv_obj_x.get()

    @x.setter
    def x(self, val):
        put_val(self.pv_obj_x, val)
            
    @property
    def xp(self):
        return self.pv_obj_xp.get()

    @xp.setter
    def xp(self, val):
        put_val(self.pv_obj_xp, val)

    @property
    def y(self):
        return self.pv_obj_y.get()

    @y.setter
    def y(self, val):
        put_val(self.pv_obj_y, val)
            
    @property
    def yp(self):
        return self.pv_obj_yp.get()

    @yp.setter
    def yp(self, val):
        put_val(self.pv_obj_yp, val)

    @property
    def z(self):
        return self.pv_obj_z.get()

    @z.setter
    def z(self, val):
        put_val(self.pv_obj_z, val)

    @property
    def pos(self):
        return np.array([self.pv_obj_z.get(), self.pv_obj_x.get()])



################################################################################
#                               Aperture Class                                 #
################################################################################

class Aperture(object):
    """
    Aperture class that can be used to clip the beam.
    """
    
    def __init__(self, pv_x_gap, pv_y_gap, pv_z):
        self.pv_obj_x_gap = Pv(pv_x_gap)
        self.pv_obj_y_gap = Pv(pv_y_gap)
        self.pv_obj_z = Pv(pv_z)
      
################################################################################
#                              Helper Functions                                #
################################################################################

def put_val(pv, val):
    try:
        pv.put(float(val))
    except ValueError:
        print("Invalid input type. Must be castable to float.")    

def distance(x1, x2):
    return np.linalg.norm(x2-x1)

################################################################################
#                              Walker Functions                                #
################################################################################
    
def d1_calc(r, theta, l1, l2, alpha1, alpha2):
    return r + l1 * (theta + alpha1) + l2 * (theta + alpha1 + alpha2)

def d2_calc(r, theta, l1, l2, l3, alpha1, alpha2):
    return r + l1*(theta + alpha1) + (l2+l3)*(theta + alpha1 + alpha2)

def alpha1_calc(r, theta, l1, l2, alpha2):
    return (-r - theta*(l1 + l2) - alpha2*l2)/(l1 + l2)

def alpha2_calc(r, theta, l1, l2, l3, alpha1):
    return (-r - theta*(l1 + l2 + l3) - alpha1*(l1 + l2 + l3))/(l2 + l3)

################################################################################
#                                     Main                                     #
################################################################################

if __name__ == "__main__":

    # PVs for (expected) variables
    # Undulator PVs
    pv_und_x = ""
    pv_und_xp = ""
    pv_und_y = ""
    pv_und_yp = ""
    pv_und_z = ""

    # M1H PVs
    pv_m1h_x = ""
    pv_m1h_alpha = ""
    pv_m1h_z = ""

    # M2H PVs
    pv_m2h_x = ""
    pv_m2h_alpha = ""
    pv_m2h_z = ""

    # P3H
    pv_p3h_img = ""
    pv_p3h_z = ""

    # DG3
    pv_dg3_img = ""
    pv_dg3_z = ""

    # Beamline Objects
    # Undulator
    undulator = Source(pv_und_x, pv_und_xp, pv_und_y, pv_und_yp, pv_und_z)
    # M1H
    m1h = Mirror(pv_m1h_x, pv_m1h_alpha, pv_m1h_z)
    # M2H
    m2h = Mirror(pv_m2h_x, pv_m2h_alpha, pv_m2h_z)
    # P3H
    p3h = Imager(pv_p3h_img, pv_p3h_z)
    # DG3
    dg3 = Imager(pv_dg3_img, pv_dg3_z)

    # Alignment procedure


