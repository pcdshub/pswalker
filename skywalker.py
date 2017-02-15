################################################################################
#                                  Skywalker                                   #
################################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from psp import Pv
from joblib import Memory
from beamDetector import Detector
from walker.iterwalk import IterWalker

################################################################################
#                                Imager Class                                  #
################################################################################

class Imager(object):
	"""
	Imager object that will encapsulate the various yag screens along the
	beamline.
	"""

	def __init__(self, pv_camera, detector=Detector()):
		self.pv_obj_camera = Pv(pv_camera)
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
	def z(self):
		return self.z

	@z.setter
	def z(self, val):
        put_val(self.z, val)



################################################################################
#                                Mirror Class                                  #
################################################################################

class Mirror(object):
	"""
	Mirror class to encapsulate the two HOMS (or any) mirrors.
	"""

	def __init__(self, pv_x, pv_xp, z):
		self.pv_obj_x     = Pv(pv_x)
		self.pv_obj_xp = Pv(pv_xp)
		self.z = z

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
	def z(self):
		return self.z

	@z.setter
	def z(self, val):
        put_val(self.z, val)

				

################################################################################
#                                Source Class                                  #
################################################################################

class Source(object):
	def __init__(self, pv_x, pv_xp, pv_y, pv_yp, z):
		self.pv_obj_x  = Pv(pv_x)
		self.pv_obj_xp = Pv(pv_xp)
		self.pv_obj_y  = Pv(pv_y)
		self.pv_obj_yp = Pv(pv_yp)
		self.z = z

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
    def x_p(self):
        return self.pv_obj_xp.get()

	@xp.setter
	def x_p(self, val):
		put_val(self.pv_obj_xp, val)

	@property
	def y(self):
		return self.pv_obj_y.get()

	@y.setter
	def y(self, val):
		put_val(self.pv_obj_y, val)
			
	@property
    def y_p(self):
        return self.pv_obj_yp.get()

	@yp.setter
	def y_p(self, val):
		put_val(self.pv_obj_yp, val)

	@property
	def z(self):
		return self.z

	@z.setter
	def z(self, val):
        put_val(self.z, val)


################################################################################
#                               Aperture Class                                 #
################################################################################

class Aperture(object):
	"""
	Aperture class that can be used to clip the beam.
	"""
    
    def __init__(self, pv_x_gap, pv_y_gap, z):
        self.pv_obj_x_gap = Pv(pv_x_gap)
        self.pv_obj_y_gap = Pv(pv_y_gap)
        self.z = z

################################################################################
#                                Walker Class                                  #
################################################################################

class Walker(object):
    def __init__(self, pv_mx, pv_my, **kwargs):
        self.pv_mx = pv_mx
        self.pv_my = pv_my
        self.lhoms = kwargs.get("lhoms", 1)
        self.agent = kwargs.get("agent", IterWalker())


        
################################################################################
#                              Helper Functions                                #
################################################################################

def put_val(pv, val):
    try:
        pv.put(float(val))
    except ValueError:
        print("Invalid input type. Must be castable to float.")	
    
if __name__ == "__main__":
    pass
