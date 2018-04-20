import time
from types import SimpleNamespace

import numpy as np
from ophyd import Device, Component, FormattedComponent

from .sim import SimDevice
from .signal import FakeSignal
from .areadetector.plugins import (StatsPlugin, ImagePlugin)
from .areadetector.detectors import PulnixDetector


class PIMPulnixDetector(PulnixDetector):
    image1 = Component(ImagePlugin, ":IMAGE1:", read_attrs=['array_data'])
    image2 = Component(ImagePlugin, ":IMAGE2:", read_attrs=['array_data'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid',
                                                            'mean_value'])

    image = SimpleNamespace(shape=[480, 620])

    def __init__(self, prefix, *, noise_x=False, noise_y=False, noise_func=None, 
                 noise_type="norm", noise_args=(), noise_kwargs={}, 
                 zero_outside_yag=False, size=(640,480), 
                 resolution=(0.0076,0.0062), **kwargs):
        super().__init__(prefix, **kwargs)
        self.noise_x = noise_x
        self.noise_y = noise_y
        self.noise_func = noise_func
        self.noise_type = noise_type
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs
        self.zero_outside_yag = zero_outside_yag
        self.size = size
        self.resolution = resolution
        # Override stats2 centroid function
        self.stats2._get_readback_centroid_x = lambda **kwargs : (
            self._get_readback_centroid_x() * self._centroid_within_bounds())
        self.stats2._get_readback_centroid_y = lambda **kwargs : (
            self._get_readback_centroid_y() * self._centroid_within_bounds())
        # Override the image size signal
        
    @property
    def centroid_x(self, **kwargs):
        """
        Returns the beam centroid in x.
        """
        self.check_camera()
        return self.stats2.centroid.x.value
        
    @property
    def centroid_y(self, **kwargs):
        """
        Returns the beam centroid in y.
        """
        self.check_camera()
        return self.stats2.centroid.y.value
          
    def _centroid_within_bounds(self):
        """
        Checks if the centroid is outside the edges of the yag.
        """
        in_x = 0 <= self.stats2.centroid.x._raw_readback <= self.image.shape[0]
        in_y = 0 <= self.stats2.centroid.y._raw_readback <= self.image.shape[1]
        if not self.zero_outside_yag or (in_x and in_y):
            return True
        return False
    
    def _get_readback_centroid_x(self):
        return self.stats2.centroid.x._raw_readback

    def _get_readback_centroid_y(self):
        return self.stats2.centroid.y._raw_readback

    @property
    def noise_x(self):
        return self.stats2.noise_x

    @noise_x.setter
    def noise_x(self, val):
        self.stats2.noise_x = bool(val)

    @property
    def noise_y(self):
        return self.stats2.noise_y

    @noise_y.setter
    def noise_y(self, val):
        self.stats2.noise_y = bool(val)

    @property
    def noise_func(self):
        return (self.stats2.noise_func_x(), self.stats2.noise_func_y())
        
    @noise_func.setter
    def noise_func(self, val):
        self.stats2.noise_func_x = val
        self.stats2.noise_func_y = val

    @property
    def noise_type(self):
        return (self.stats2.noise_type_x, self.stats2.noise_type_y)

    @noise_type.setter
    def noise_type(self, val):
        self.stats2.noise_type_x = val
        self.stats2.noise_type_y = val

    @property
    def noise_args(self):
        return (self.stats2.noise_args_x, self.stats2.noise_args_y)

    @noise_args.setter
    def noise_args(self, val):
        self.stats2.noise_args_x = val
        self.stats2.noise_args_y = val

    @property
    def noise_kwargs(self):
        return (self.stats2.noise_kwargs_x, self.stats2.noise_kwargs_y)

    @noise_kwargs.setter
    def noise_kwargs(self, val):
        self.stats2.noise_kwargs_x = val
        self.stats2.noise_kwargs_y = val

    @property
    def size(self):
        return (self.cam.size.size_x.value, self.cam.size.size_y.value)

    @size.setter
    def size(self, val):
        self.image1._image = lambda : np.zeros(val)
        self.cam.size.size_x.put(val[0])
        self.cam.size.size_y.put(val[1])

    @property
    def resolution(self):
        return (self.cam.resolution.resolution_x.value, 
                self.cam.resolution.resolution_y.value)

    @resolution.setter
    def resolution(self, val):
        self.cam.resolution.resolution_x.put(val[0])
        self.cam.resolution.resolution_y.put(val[1])


class PIMMotor(Device):
    states = Component(FakeSignal, value="OUT")
    # A new component to keep track of actual y positions
    _pos = Component(FakeSignal, value=0)

    def __init__(self, prefix, pos_in=0, pos_diode=0.5, pos_out=1, 
                 settle_time=0, velocity=None, noise=False, noise_func=None,
                 noise_type="uni", noise_args=(), noise_kwargs={}, timeout=None,
                 **kwargs):
        super().__init__(prefix, **kwargs)
        if pos_diode < pos_in:
            pos_diode = pos_in + 0.5
        if pos_out < pos_diode:
            pos_out = pos_diode + 0.5
        self.pos_d = {"DIODE":pos_diode, "OUT":pos_out, 
                      "IN":pos_in, "YAG":pos_in}
        self.timeout = timeout
        self.settle_time = settle_time
        self.velocity = velocity
        self.noise = noise
        self.noise_func = noise_func
        self.noise_type = noise_type
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs
        self._pos._get_readback = lambda : self.pos_d.get(self.position)
    
    def move(self, position, **kwargs):
        if isinstance(position, str):
            if position.upper() in ("DIODE", "OUT", "IN", "YAG"): 
                self.states.put("Unknown")
                if position.upper() == "IN":
                    pos = "YAG"
                else:
                    pos = position.upper()
                status = self.states.set(position.upper(), timeout=self.timeout)
                time.sleep(0.1)
            # Match the inputted state in y
            self._pos.put(self.pos_d[position.upper()])
            return status
        raise ValueError("Position must be a PIM valid state.")

    set = move

    @property
    def position(self):
        pos = self.states.value
        if pos == "YAG":
            return "IN"
        return pos

    @property
    def blocking(self):
        return self.position == 'IN'

    @property
    def settle_time(self):
        if callable(self._pos.put_sleep):
            return self._pos.put_sleep()
        return self._pos.put_sleep

    @settle_time.setter
    def settle_time(self, val):
        self._pos.put_sleep = val

    @property
    def velocity(self):
        return self._pos.velocity

    @velocity.setter
    def velocity(self, val):
        self._pos.velocity = val

    @property
    def noise(self):
        return self._pos.noise

    @noise.setter
    def noise(self, val):
        self._pos.noise = bool(val)

    @property
    def noise_func(self):
        return self._pos.noise_func
    
    @noise_func.setter
    def noise_func(self, val):
        self._pos.noise_func = val

    @property
    def noise_type(self):
        return self._pos.noise_type

    @noise_type.setter
    def noise_type(self, val):
        self._pos.noise_type = val

    @property
    def noise_args(self):
        return self._pos.noise_args

    @noise_args.setter
    def noise_args(self, val):
         self._pos.noise_args = val

    @property
    def noise_kwargs(self):
        return self._pos.noise_kwargs

    @noise_kwargs.setter
    def noise_kwargs(self, val):
        self._pos.noise_kwargs = val


class PIM(PIMMotor, SimDevice):
    detector = FormattedComponent(PIMPulnixDetector, 
                                  "{self._section}:{self._imager}:CVV:01",
                                  read_attrs=['stats2'])
    def __init__(self, prefix, x=0, y=0, z=0, noise=0, settle_time=0, 
                 centroid_noise=False, size=(640,480), 
                 resolution=(0.0076,0.0062), zero_outside_yag=False, **kwargs):
        self._section=prefix
        self._imager=prefix
        if len(prefix.split(":")) < 2:
            prefix = "TST:{0}".format(prefix)
        super().__init__(prefix, pos_in=y, noise=noise, 
                         settle_time=settle_time, **kwargs)

        # Simulation Values
        self.sim_x.put(x)
        self.sim_y._get_readback = lambda : self._pos.value
        self.sim_z.put(z)
        self.log_pref = "{0} (PIM) - ".format(self.name)
        # Detector args
        self.zero_outside_yag = zero_outside_yag
        self.resolution = resolution
        self.size = size
        self.centroid_noise = centroid_noise
        
    @property
    def centroid_noise(self):
        return (self.detector.noise_x, self.detector.noise_y)

    @centroid_noise.setter
    def centroid_noise(self, val):
        self.detector.noise_x = bool(val)
        self.detector.noise_y = bool(val)

    @property
    def size(self):
        return self.detector.size

    @size.setter
    def size(self, val):
        self.detector.size = val

    @property
    def resolution(self):
        return self.detector.resolution
        
    @resolution.setter
    def resolution(self, val):
        self.detector.resolution = val

    @property
    def zero_outside_yag(self):
        return self.detector.zero_outside_yag
        
    @zero_outside_yag.setter
    def zero_outside_yag(self, val):
        self.detector.zero_outside_yag = bool(val)
    
