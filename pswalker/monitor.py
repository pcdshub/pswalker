# Monitor and Logging Module for Skywalker

import pandas as pd

class Monitor(object):
	"""
	Monitor class that writes the EPICS data to some place that can is
	retrievable by the other components.
	
	Whenever it receives the okay from walker, it is supposed to save the alpha
	positions of the mirrors and as well as the beam position at whichever imager
	is inserted.

	It should then be able to export the data as a pandas DataFrame or some way
	that makes querying for info easy.
	"""
	
	def __init__(self, **kwargs):
        self._all_data = pd.DataFrame()

	def get_all_data(self):
		"""Return the full contents of the log."""
		pass
	
	def get_last_n_points(self, n):
		"""Returns the last n entries of data."""
		pass

    @property
    def current_centroid(self):
        """
        Get the most recent entry of centroids and return them as a tuple.
        """
        return None, None
        
