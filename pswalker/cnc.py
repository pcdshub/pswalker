# Command and Control Module for Skywalker

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from monitor import Monitor
from walker import Walker
from modelbuild import ModelBuilder

class CNC(object):
	"""
	Command and control class that interacts with the user and performs the
	alignment.
	"""
	
	def __init__(self, **kwargs):
		self.monitor = kwargs.get("monitor", Monitor())
		self.walker = kwargs.get("walker", Walker())
		self.model_builder = kwargs.get("model_builder", ModelBuilder())
		self.model = kwargs.get("model", None)
		self.iter_walker = kwargs.get("iter_walker", None)
		self.model_walker = kwargs.get("model_walker", None)
		self.p1 = kwargs.get("p1", None)
		self.p2 = kwargs.get("p2", None)
	
	def modelbuild(self, load_model=None):
		"""
		Runs the model building => modelwalk loop
		"""
		# Tell the model builder what points we want to align to
		self.model_builder.p1 = self.p1
		self.model_builder.p2 = self.p2

		# Load the model from a saved module
		if load is not None:
			self.model = self.model_builder.load(load_model)

		# Create a new iter walker instance if we havent already
		if self.iter_walker is None:
			self.iter_walker = IterWalker(self.walker, self.model)
		
		# Perform the alignment using the walker
		self.iter_walker.align(do_move=True)
	
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
	
