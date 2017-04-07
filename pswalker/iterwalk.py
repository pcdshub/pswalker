# Iterwalk Module for Skywalker


class IterWalker(object):
	"""
	IterWalker class that integrates with walker to perform a sequence of closed
	loop moves to reach the goal pixel at each imager.
	"""

	def __init__(self):
		pass

    def step(self):
        """
        Return *both* alphas for next step. Only one of them has to be different
        though. This is done to unify the interface to walker.
        """
        raise NotImplementedError
