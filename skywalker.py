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
from walker import IterWalk

################################################################################
#                                Imager Class                                  #
################################################################################

class Imager(Object):
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
	def centroid(self):
		"""Return the centroid of the image."""
		self.centroid, self.bounding_box = self.detector.find(Pv.get())
		return self.centroid

################################################################################
#                                Mirror Class                                  #
################################################################################

class Mirror(Object):
	"""
	Mirror class to encapsulate the two HOMS (or any) mirrors.
	"""

	def __init__(self, pv_x, pv_pitch):
		self.x     = Pv(pv_x)
		self.pitch = Pv(pv_pitch)

################################################################################
#                                   Source                                     #
################################################################################

class Source(Object):
	pass


################################################################################
#                                   Walker                                     #
################################################################################

class Walker(Object):
	pass

if __name__ == "__main__":
    pass
