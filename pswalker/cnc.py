# Command and Control Module for Skywalker

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from monitor import Monitor
from walker import Walker
from modelbuild import ModelBuilder

from utils.exceptions import CNCException

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

        self.load_model = kwargs.get("load_model", None)
        
    def modelbuild(self):
        """
        Runs the model building => modelwalk loop
        """
        raise NotImplementedError

    def _set_goal_points(self, model):
        model.p1 = self.p1
        model.p2 = self.p2
        return model
        
    def _load(self, saved_model):
        model_module = importlib.import_module("pswalker.models.{0}".format(saved_model))
        model = model_module.get_model()
        model = self._set_goal_points(model)
        return model
        
    def modelwalk(self):
        """
        Runs the modelwalk loop.
        """
        
        if self.load_model:
            # Load the model from a saved module
            self.model = self._load(load_model)
        elif self.model is None:
            raise CNCException

        # Create a new model walker instance if we havent already
        if self.model_walker is None:
            self.model_walker = ModelWalker(self.walker, self.model)
        # Perform the alignment using the walker
        self.model_walker.align(do_move=True)


    def iterwalk(self):
        """
        Runs the iterwalk loop.
        """
        raise NotImplementedError
