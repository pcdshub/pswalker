############
# Standard #
############
from collections import OrderedDict
###############
# Third Party #
###############
import numpy as np
from bluesky.examples import Mover, Reader

##########
# Module #
##########

class OneMirrorSystem(object):
    """
    System of a source, mirror and an imager.
    """
    def __init__(self, **kwargs):
        self._x0 = kwargs.get("x0", 0)
        self._xp0 = kwargs.get("xp0", 0)
        self._x1 = kwargs.get("x1", 0)
        self._d1 = kwargs.get("d1", 90.510)
        self._a1 = kwargs.get("a1", 0.0014)
        self._x2 = kwargs.get("x2", 0.0317324)
        self._d2 = kwargs.get("d2", 101.843)
        self._noise_x0 = kwargs.get("noise_x0", 0)
        self._noise_xp0 = kwargs.get("noise_xp0", 0)
        self._noise_x1 = kwargs.get("noise_x1", 0)
        self._noise_d1 = kwargs.get("noise_d1", 0)
        self._noise_a1 = kwargs.get("noise_a1", 0)
        self._noise_x2 = kwargs.get("noise_x2", 0)
        self._noise_d2 = kwargs.get("noise_d2", 0)
        self._fake_sleep_m1 = kwargs.get("fake_sleep_m1", 0)
        self._name_s = kwargs.get("name_s", "Source")
        self._name_m1 = kwargs.get("name_m1", "Mirror 1")
        self._name_y1 = kwargs.get("name_y1", "YAG 1")
        self._pix_y1 = kwargs.get("pix_y1", (1392, 1040))
        self._size_y1 = kwargs.get("size_y1", (0.0076, 0.0062))
        self._inverted_y1 = kwargs.get("inverted_y1", False)

        self.source = Source(self._name_s, self._x0, self._xp0)
        
        self.mirror_1 = Mirror(self._name_m1, self._x1, self._a1, self._d1,
                               noise_position=self._noise_x1,
                               noise_pitch=self._noise_a1,

        self.yag_1 = YAG(self._name_y1, self._x2, self._d2, self._noise_x2,
                         self._noise_d2, pix=self._pix_y1, size=self._size_y1)
        
        def calc_cent_x():
            x = -2*self.mirror_1.alpha*self.mirror_1.z + \
              2*self.mirror_1.alpha*self.yag_1.z - \
              self.yag_1.z*self.source.xp + 2*self.mirror_1.x - self.source.x

            return np.floor(self.yag_1.pix[0]/2) + \ 
              (x - self.x2)*self.yag_1.pix[0]/self.yag_1.size[0]
            
        self.yag_1.cent_x = calc_cent_x

class Source(Mover):
    """
    Simulation of the photon source (simplified undulator).
    """
    def __init__(self, name, x, xp):
        self.name = name
        self.x = x
        self.xp = xp
 
        def position(val):
            if noise_x:
                val += np.random.uniform(-1, 1)*noise_x
            self.x = val
            return self.x
        
        def pointing(val):
            if noise_z:
                val += np.random.uniform(-1, 1)*noise_z
            self.xp = val
            return self.xp

        super().__init__(
            self.name, OrderedDict(
                [('x', position),
                ('xp', pointing),
                ('x_setpoint', lambda x : x),
                ('xp_setpoint', lambda x : x)],
            {'x':self.x, 'xp':self.xp}, fake_sleep=fake_sleep)


class Mirror(Mover):
    """
    Simulation of the Flat Mirror Pitch

    Parameters
    ----------
    name : string
        Name of motor

    initial_position : float
    	Initial x position of the motor in meters from nominal

    initial_pitch : float
        Initial pitch of motor in microradians

    distance : float
    	Distance of the mirror from the source in meters

    noise_position : float, optional
        Scaler to multiply uniform noise on position 

    noise_pitch : float, optional
        Scaler to multiply uniform noise on pitch

    fake_sleep, float, optional
        Simulate moving time
    """
    def __init__(self, name, x, z, alpha, noise_x=None, noise_z=None, 
                 noise_alpha=None, fake_sleep=0):
        self.name = name
        self.x = x
        self.z = z
        self.alpha = alpha
        self.noise_x = noise_x
        self.noise_z = noise_z
        self.noise_alpha = noise_alpha

        def position(val):
            if noise_x:
                val += np.random.uniform(-1, 1)*noise_x
            self.x = val
            return self.x
        
        def distance(val):
            if noise_z:
                val += np.random.uniform(-1, 1)*noise_z
            self.z = val
            return self.z

        def pitch(val):
            if noise_alpha:
                val += np.random.uniform(-1, 1)*noise_alpha
            self.alpha = val
            return self.alpha

        super().__init__(
            self.name, OrderedDict(
                [('x', position),
                ('z', distance),
                ('alpha', pitch),
                ('x_setpoint', lambda x : x),
                ('z_setpoint', lambda x : x),
                ('alpha_setpoint', lambda x : x)]),
            {'x':self.x, 'z':self.z, 'alpha':self.alpha}, fake_sleep=fake_sleep)
        
class YAG(Reader):
    """
    Simulation of a single bounce YAG

    The model makes the assumption that we have a single mirror and a
    downstream YAG, whose edge is left edge is hit when the position of the
    motor is zero.

    Parameters
    ----------
    name : str
        Alias of YAG

    motor : Positioner
        Simulated pitch of mirror

    motor_field : str
        Name of motor_field to calculate centroid position. Value should be
        expressed in microns

    distance : float
        Distance from mirror to YAG in meters

    inverted : bool, optional
        Whether the image is reflected before being imaged by the camera

    noise_multiplier : float, optional
        Introduce unifrom random noise to the pixel location
    """
    def __init__(self, name, motor, motor_field,
                 distance, inverted=False,
                 noise_multiplier=None, **kwargs):
        
        self.name = name
        self._x = x
        self.z = z
        self.noise_x = noise_x
        self.noise_z = noise_z

        self.pix = kwargs.get("pix", (1392, 1040))
        self.size = kwargs.get("size", (0.0076, 0.0062))
        
        def position(val):
            if noise_x:
                val += np.random.uniform(-1, 1)*noise_x
            self.x = val
            return self.x
        
        def distance(val):
            if noise_z:
                val += np.random.uniform(-1, 1)*noise_z
            self.z = val
            return self.z
        
        def cent_x():
            return np.floor(self.pix[0]/2)
        
        def cent_y():
            return np.floor(self.pix[1]/2)

        def cent():
            return (cent_x(), cent_y())

        self.motor = Mover(self.name+" Motor", {'x', position}, {'x':self._x})

        super().__init__(self.name, {'centroid_x' : cent_x,
                                     'centroid_y' : cent_y,
                                     'centroid' : cent}, **kwargs)

    @property
    def x(self):
    	return self.motor.read()[self.motor_field]['value']
    
    @x.setter
    def x(self, val):
    	self.motor.set(val)

                                        
