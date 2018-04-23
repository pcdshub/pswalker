"""
Overrides for Epics Signals
"""
import time
import logging

import numpy as np

from ophyd.signal import Signal


class FakeSignal(Signal):
    """
    Empty signal class with some extra features to better simulate real devices.
    
    The main additions are the ability to noise to the readback, add static 
    sleep times to the read or set, add sleep time on every set based on a 
    velocity parameter, and setting the value of the signal according to an
    outside function/method.
    """
    def __init__(self, value=0, put_sleep=0, get_sleep=0, 
                 noise=False, noise_type="norm", noise_func=None, noise_args=(), 
                 noise_kwargs={}, velocity=None, use_string=False, **kwargs):
        self.put_sleep = put_sleep
        self.get_sleep = get_sleep
        self.noise = bool(noise)
        self.noise_type = noise_type
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs
        self.velocity = velocity
        self.use_string = use_string
        self._supported_noise_types = {"uni" : self.noise_uni, 
                                       "norm" : self.noise_norm}
        self._check_noise_args = {"uni" : self._check_args_uni,
                                  "norm" : self._check_args_norm}
        
        # If a custom noise function is supplied use that
        if noise_func:
            self._check_args_not_none()
            self._noise_func = lambda : noise_func(*self.noise_args,
                                                   **self.noise_kwargs)
        # Otherwise check the noise type and use a default
        elif self.noise_type.lower() not in self._supported_noise_types.keys():
            logging.warning("Inputted noise type not supported. Must be one of "
                            "the following: {0}.\nSetting to 'uni'.".format(
                                self._supported_noise_types.keys()))
            self.noise_type = "uni"
        if self.noise_type.lower() in self._supported_noise_types.keys():
            self._check_noise_args[self.noise_type]()
            self._noise_func = lambda : self._supported_noise_types[
                self.noise_type](*self.noise_args, **self.noise_kwargs)
        super().__init__(value=value, **kwargs)

    def _check_args_not_none(self, args=(), kwargs={}):
        """
        Checks if the noise args or the kwargs are set to None. They are
        replaced with an empty tuple and dictionary or the inputted args or
        kwargs.
        """
        if not self.noise_args:
            self.noise_args = args
        if not self.noise_kwargs:
            self.noise_kwargs = kwargs

    def _check_args_uni(self):
        """
        Sets default values for numpy.random.uniform. See URL below for 
        full documentation:

        https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.uniform.html
        """
        self._check_args_not_none((-1, 1), {})

    def _check_args_norm(self):
        """
        Sets default values for numpy.random.normal. See URL below for full 
        documentation:
        
        https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.normal.html
        """
        self._check_args_not_none((0, 0.25), {})
            

    def put(self, value, **kwargs):
        # Wait using the velocity
        if not self.use_string:
            try:
                time_to_dest = 0
                if callable(self.velocity):
                    if self.velocity():
                        time_to_dest = ((value - self._raw_readback) / 
                                        self.velocity())
                elif self.velocity is not None:
                    time_to_dest = (value - self._raw_readback) / self.velocity
                time.sleep(time_to_dest)
            except TypeError:
                if isinstance(value , str):
                    self.use_string = True
                else:
                    raise
        # Wait before putting
        try:
            time.sleep(self.put_sleep)
        except TypeError:
            time.sleep(self.put_sleep())
        return super().put(value, **kwargs)

    def get(self, **kwargs):
        # Wait before getting
        try:
            time.sleep(self.get_sleep)
        except TypeError:
            time.sleep(self.get_sleep())
        return super().get(**kwargs)

    @property
    def _readback(self):
        if not self.use_string:
            try:
                return self._get_readback() + self._noise_func() * self.noise
            except TypeError:
                if isinstance(self._get_readback(), str):
                    self.use_string = True
                else:
                    raise
        return self._get_readback()

    @_readback.setter
    def _readback(self, value):
        self._put_readback(value)

    def _get_readback(self, **kwargs):
        """
        Placeholder method that can be overridden to calculate the returned
        readback.
        """
        return self._raw_readback

    def _put_readback(self, value, **kwargs):
        """
        Placeholder method that can be overridden to calculate the raw readback 
        value that will be set.
        """
        self._raw_readback = value

    def noise_uni(self, *args, **kwargs):
        """
        Wrapper for numpy.random.uniform. See URL below for full documentation:

        https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.uniform.html
        """
        scale = kwargs.pop("scale", self.noise)
        return np.random.uniform(*args, **kwargs) * scale

    def noise_norm(self, *args, **kwargs):
        """
        Wrapper for numpy.random.normal. See URL below for full documentation:
        
        https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.normal.html
        """
        scale = kwargs.pop("scale", self.noise)
        return np.random.normal(*args, **kwargs) * scale

    def stop(self, *args, **kwargs):
        """
        A hack to appease bluesky.
        """
        pass
    
    

