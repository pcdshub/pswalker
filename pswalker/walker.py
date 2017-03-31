"""
Walker module that contains the class that allows the various walkers to 
interface with the hardware components.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from epics import caget
from beamDetector.detector import Detector
from utils.cvUtils import to_uint8, plot_image

################################################################################
#                                 Walker Class                                 #
################################################################################

class Walker(object):
    pass


################################################################################
#                                 Imager Class                                 #
################################################################################

class Imager(object):
    """
    Imager object that will encapsulate the various yag screens along the
    beamline. 
    """

    def __init__(self,**kwargs):
        self.x = kwargs.get("x", None)
        self.z = kwargs.get("z", None)
        self.detector = kwargs.get("det", Detector(prep_mode="clip"))
        self.image    = None
        self.image_xsz = 0
        self.image_ysz = 0
        self.centroid = None
        self.bounding_box = None
        self.pos = np.array([self.z, self.x])
        self._scale = None
        self.sum = None
        self.beam = False
        self.inserted = False
        self.mppix = kwargs.get("mppix", 1.25e-5)

        self.insert_val = kwargs.get("insert", 0.0)
        self.remove_val = kwargs.get("remove", 0.0)
        # self.image_sz = kwargs.get("img_sz", 0.0005)
        self.pv_yag = kwargs.get("yag", None)
        self.pv_camera = kwargs.get("camera", None)
        self.simulation = kwargs.get("simulation", False)
        
        self._check_args()

    def _check_args(self):
        pass

    def get_image(self, norm="clip"):
        """Get a new image from the imager."""
        if self.simulation:
	        try:
	            uint_norm = to_uint8(self.image, "norm")
	            self._scale = self.image.sum() / self.sum
	            self.image_ysz, self.image_xsz  = self.image.shape
	            return to_uint8(uint_norm * self._scale, "clip")
	        except TypeError:
	            self.sum = self.image.sum()
	            return self.get_image(norm=norm)
	    else:
	        self.image = to_uint8(caget(self.pv_camera), norm)
	        return self.image

	def get_beam(self, norm="clip", cent=True, bbox=True):
	    """Return beam info (centroid and bounding box) of the saved image."""
        try:
            self.centroid, self.bounding_box = self.detector.find(self.image)
            self.beam = True
            if cent and bbox:
                return self.centroid, self.bounding_box
            elif cent:
                return self.centroid
            elif bbox:
                return self.bounding_box
            else:
                raise Exception
        except IndexError:
            self.beam = False
            return None
	    
    def get_centroid(self, norm="clip"):
        """Return the centroid of the stored image."""
        return self.get_beam(norm, cent=True, bbox=False)

    def get_bounding_box(self, norm="clip"):
        """Return the bounding box of the stored image."""
        return self.get_beam(norm, cent=False, bbox=True)
        
    def get_image_and_centroid(self, norm="clip"):
        """Get a new image and return the centroid."""
        self.get_image(norm)
        return self.get_centroid(self, norm)

    def get_image_and_bounding_box(self, norm="clip"):
        """Get a new image and return the bounding box."""
        self.get_image(norm)
        return self.get_bounding_box(self, norm)

    def get_image_and_beam(self, norm="clip"):
        """Get a new image and return both the centroid and bounding box."""
        self.get_image(norm)
        return self.get_beam(self, norm)

    def insert(self):
        """Moves the yag to the inserted position."""
        pass
    
    def remove(self):
        """Moves the yag to the removed position."""
        pass

################################################################################
#                                 Mirror Class                                 #
################################################################################

class Mirror(object):
    """
    Mirror class to encapsulate the two HOMS (or any) mirrors.
    """

    def __init__(self, x, alpha, z):
        self.x = x
        self.alpha = alpha
        self.z = z
        self.pos = np.array([self.z, self.x])

################################################################################
#                                 Source Class                                 #
################################################################################

class Source(object):
    def __init__(self, x, xp, y, yp, z):
        self.x  = x
        self.xp = xp
        self.y  = y
        self.yp = yp
        self.z = z
        self.pos = np.array([self.z, self.x])
