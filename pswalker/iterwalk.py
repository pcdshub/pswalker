# Iterwalk Module for Skywalker

from __future__ import absolute_import
from __future__ import division

import numpy as np

# Using base iterwalker exceptions for now. Implement more detailed excs later
from .utils.exceptions import IterWalkException

class IterWalker(object):
    """
    IterWalker class that aligns the mirrors by iteratively optimizing the mirror
    positions.
    """
    # For the initial implementation of iterwalker, all it will do is call the
    # jog_alphas_to_pixels walker method. This is the simplest and most
    # intuitive way to implement the iterative walk so it may be best to keep it
    # like this. However I initially thought that there may be an advantage to
    # moving to a specific alpha instead and came up with the scheme below,
    # which is more or less modelwalk-lite. It was only as I was adding the
    # notes to walker.py that I started to think that this may not add enough
    # value to be worth the time to write it out. So for now I will leave this
    # here along with this module, but I'm now questioning if the module even
    # needs to exist.

    # Smarter IterWalk (ModelWalk-Lite):
    
    # For the first move on each motor, it will take increasingly large step sizes
    # in some direction until the beam has noticeably moved on the imager (where
    # noticeably means maybe 5ish pixels). It will then do a linear fit on the two
    # (or more) points obtained from the move and use that to calculate the alpha
    # necessary to move to the desired point. The eq will have the form:

    # x0 + x1*a1 + x2*a2

    # fitting to x0, x1, and x2. For the first few moves, instead of moving all 
    # the way it will only move 1/2-3/4ths of the way to the point as a way to 
    # prevent overshooting due to poor curve fitting. The fit is then refined 
    # using that move to then make a final move to the goal point.
    def __init__(self, walker, monitor, **kwargs):
        self.walker = walker
        self.monitor = monitor

        self.p1 = kwargs.get("p1", 0)
        self.p2 = kwargs.get("p2", 0)

        self.mode = kwargs.get("mode", "jog")

        # self.first_move = kwargs.get("first_move", 1e-9) # First proposed step        
        # self._goal_points = np.array((self.p1, self.p2))
        # self._turn = False      # False is alpha1's turn, True is alpha2
        # self._n_moves = np.array((0,0))
        # self._n_iters = np.array((0,0))
        # self._scale = np.sqrt(10)

    def step(self, **kwargs):
        """
        Return *both* alphas for next step. Only one of them has to be different
        though. This is done to unify the interface to walker.
        """        
        # if self._turn is "alpha1":
        #     dist = self._dist_from_goal[0]
        #     # If this is the first move made, then make a small test move to see
        #     # how much the beam moves at the imager
        #     # Then use this to propose a move to the point.            
        # elif self._turn is "alpha2":
        #     dist = self._dist_from_goal[1]
        #     pass
        # else:
        #     raise IterWalkerException("How did you do that?")

        mirror_1 = kwargs.get("mirror_1", False)
        mirror_2 = kwargs.get("mirror_2", False)

        if self.mode is "jog":
            current_centroids = self.monitor.current_centroids
            if mirror_1 is True:
                self.walker.jog_alphas_to_pixels(self.p1, current_centroids[1])
            elif mirror_2 is True:
                self.walker.jog_alphas_to_pixels(current_centroids[0], self.p2)
            else:
                raise IterWalkerException
        else:
            raise NotImplementedError
        
        # dist = self._dist_from_goal[turn_idx]
        # step_alpha = self.monitor.current_alphas[turn_idx]

        # # If this is first turn on the first iteration, do a simple fit on the
        # # current position and the first "registered" move position
        # if self._n_moves[turn_idx] == 0 and self._n_iters[turn_idx] == 0:
        #     # Propose the first move            
        #     # If it doesn't register (centroid hasnt shifted by at least 5),
        #     # propose a another move 3.33.. times as large.
        #     # Do a fit on all moves according to
        #     #     x0 + x1*a1 + x2*a2            
        #     # Propose another move using the fit that reaches            
        #     pass

        # # After this, do a fit on the full eq using all data since the start of
        # # the 
                
    # @property
    # def _dist_from_goal(self):
    #     return self.monitor.current_centroids - self._goal_points

        
