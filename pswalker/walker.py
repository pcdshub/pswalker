"""
Walker module that contains the class that allows the various walkers to 
interface with the hardware components.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import warnings
import numpy as np

from bluesky import RunEngine
from bluesky.plans import scan
from ophyd import EpicsMotor
from .components import Imager, FlatMirror, Linac

################################################################################
#                                 Walker Class                                 #
################################################################################

class Walker(object):
    """
    Walker class that will actually perform the motions proposed by iterwalk or
    modelwalk. High level methods will call lightpath functions for lower level
    functionality (insert, remove and various checks).
    """

    def __init__(self, monitor, **kwargs):
        # This should be linked somehow to the templated models. A simple idea
        # is for walker to be a class that (dynamically?) inherits from the
        # model template that represents the system. For now I kept them separate
        # to avoid "premature optimization"
        self.monitor = monitor
        self.source = kwargs.get("source", Linac())
        self.mirror_1 = kwargs.get("mirror_1", FlatMirror())
        self.mirror_2 = kwargs.get("mirror_2", FlatMirror())
        self.imager_1 = kwargs.get("imager_1", Imager())
        self.imager_2 = kwargs.get("imager_2", Imager())
        self.p1 = kwargs.get("p1", 0)   #Desired point at imager 1
        self.p2 = kwargs.get("p2", 0)   #Desired point at imager 2
        self.tolerance = kwargs.get("tolerance", 5e-9)
        self.step_size = kwargs.get("step_size", 1e-7)

    def _move_alpha(self, new_alpha, mirror):
        """Performs the necessary steps to do a move of mirror 1."""
        alpha = self.monitor.current_alphas[mirror]
        # Only perform the move if it is to a position outside the tolerance
        if new_alpha < alpha-self.tolerance or new_alpha > alpha+self.tolerance:
            # There are two objectives for a move made by walker:
            # 1) Get to the goal
            # 2) Archive data from the move

            # The first is simple. A proposal for the second would be to do a
            # scan of n points between current_alpha1 and new_alpha1 and then at
            # each point store alpha1, alpha2 and pixel position on the
            # imager(s).

            # This seems like a slight variation on some of the canonical
            # bluesky scan demo so if that isn't what we are doing, why not?
            raise NotImplementedError

    def move_alphas(self, new_alpha_1, new_alpha_2):
        """Moves mirrors 1 and 2 to the inputted pitches."""
        # TODO: (Try to) Use multiprocessing to perform the moves simultaneously
        self._move_alpha(new_alpha_1, 0)
        self._move_alpha(new_alpha_2, 1)

    def move_rel_alphas(self, rel_alpha_1, rel_alpha_2):
        """Moves mirrors 1 and 2 by the inputted pitches."""
        alphas = self.monitor.current_alphas
        # TODO: (Try to) Use multiprocessing to perform the moves simultaneously        
        self._move_alpha(alphas[0] + rel_alpha_1, 0)
        self._move_alpha(alphas[1] + rel_alpha_2, 1)

    def _jog_alpha_to_pixel(self, new_pixel, mirror):
        """
        Jogs the inputted mirror pitch until the beam centroid reaches the
        desired pixel.
        """
        current_centroid = self.monitor.current_centroids[mirror]
        # Only perform the move if it is to a different pixel than where it is
        if current_centroid != new_pixel:
            # Determine which direction to jog
            # Set up a monitor on the pv for beam centroidx
            # Run twf or twr depending on direction until pv monitor reads the
            # same centroid pixel as desired one
            raise NotImplementedError
        
    def jog_alphas_to_pixels(self, new_pixel_1, new_pixel_2):
        """
        Jogs each mirror until the centroid on the respective imager reaches
        the desired pixel.
        """
        # TODO: (Try to) Use multiprocessing to perform the moves simultaneously
        self._jog_alpha_to_pixel(new_pixel_1, 0)
        self._jog_alpha_to_pixel(new_pixel_2, 1)

