# Iterwalk Module for Skywalker

import numpy as np

from utils.exceptions import IterWalkerException

class IterWalker(object):
    """
    IterWalker class that aligns the mirrors by iteratively optimizing the mirror
    positions.
    """

    def __init__(self, walker, monitor, **kwargs):
        self.walker = walker
        self.monitor = monitor

        self.p1 = kwargs.get("p1", 0)
        self.p2 = kwargs.get("p2", 0)
        
        self._goal_points = np.array((self.p1, self.p2))

        self._turn = 0
        self._n_moves = np.array((0,0))
        self._n_iters = np.array((0,0))

    def step(self):
        """
        Return *both* alphas for next step. Only one of them has to be different
        though. This is done to unify the interface to walker.
        """
        
        if self._turn is "alpha1":
            dist = self._dist_from_goal[0]
            # If this is the first move made, then make a small test move to see
            # how much the beam moves at the imager

            # Then use this to propose a move to the point.
            
        elif self._turn is "alpha2":
            dist = self._dist_from_goal[1]

            pass
        else:
            raise IterWalkerException("How did you do that?")

    @property
    def _dist_from_goal(self):
        return self.monitor.current_centroids - self._goal_points

        
