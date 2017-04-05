# Command and Control Module for Skywalker

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from monitor import Monitor
from walker import Walker

class CNC(object):
	"""
	Command and control class that interacts with the user and performs the
	alignment.
	"""
	
	def __init__(self):
		self.monitor = Monitor()
		self.walker = Walker()

	def _build_model(self):
		"""
		Method that builds a model using the data from the logger.
		"""
		pass
	
	def modelbuild(self):
		"""
		Runs the model building => modelwalk loop
		"""
		
		pass
	
	def modelwalk(self):
		"""
		Runs the modelwalk loop.
		"""
		pass

	def iterwalk(self):
		"""
		Runs the iterwalk loop.
		"""
		pass
	
