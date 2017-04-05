# ModelBuilder component of Skywalker

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pandas as pd
import numpy as np



class ModelBuilder(object):
	"""
	Class that builds beamline models to be used by ModelWalker.
	"""
	
	def __init__(self, **kwargs):
		pass


	def get_move_logs(self):
		# Performs the steps necessary to obtain the move logs
		pass
	
	def get_imager_1_logs(self):
		# Parses the logs to get a table of logs going from 
		# alpha1, alpha2 => pixe on imager 2
		pass

	def get_imager_2_logs(self):
		# Parses the logs to get a table of logs going from 
		# alpha1, alpha2 => pixel on imager 2
		pass

	
	
