# Monitor and Logging Module for Skywalker

import pandas as pd

# Using base monitor exceptions for now. Implement more detailed excs later
from utils.exceptions import MonitorException

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

        self._cached_centroids = np.zeros(2)
        self._cached_alphas = np.zeros(2)

    def get_all_data(self):
        """Return the full contents of the log."""
        pass
    
    def get_last_n_points(self, n):
        """Returns the last n entries of data."""
        pass

    def update(self):
        """
        Saves the current positions of the mirrors and the beam position on
        whatever imager is inserted.
        """
        self._new_data = True
        # Do the update
        pass

    @property
    def current_centroids(self):
        """
        Get the most recent entry of centroids and return as a numpy array.

        Use a simple caching system so as to not recompute the same
        """
        if self._new_centroids:
            # Grab most recent entries to the dataframe
            # centroids = self._all_data[['cent1','cent2']].tail(1)
            # self._cached_centroids = np.array(centroids)
            self._new_centroids = False
        return self._cached_centroids
       
    @property
    def current_alphas(self):
        """
        Get the most recent entry of mirror pitches and return as a numpy array. 
        """
        if self._new_alphas:
            # Grab most recent entries to the dataframe
            # alphas = self._all_data[['alpha1','alpha2']].tail(1)
            # self._cached_alphas = np.array(alphas)
            self._new_alphas = False
        return self._cached_alphas


    @property
    def _new_data(self):
        return self._new_data

    @_new_data.setter
    def _new_data(self, val):
        if isinstance(val, bool):
            self._new_centroids = val
            self._new_alphas = val
        else:
            raise MonitorException
