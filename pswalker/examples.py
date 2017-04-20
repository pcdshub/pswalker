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
        self.x0 = kwargs.get("x0", 0)
        self.xp0 = kwargs.get("xp0", 0)
        self.x1 = kwargs.get("x1", 0)
        self.d1 = kwargs.get("d1", 90.510)
        self.a1 = kwargs.get("a1", 0.0014)
        self.x2 = kwargs.get("x2", 0.0317324)
        self.d2 = kwargs.get("d2", 101.843)
        self.noise_x0 = kwargs.get("noise_x0", 0)
        self.noise_xp0 = kwargs.get("noise_xp0", 0)
        self.noise_x1 = kwargs.get("noise_x1", 0)
        self.noise_d1 = kwargs.get("noise_d1", 0)
        self.noise_a1 = kwargs.get("noise_a1", 0)
        self.noise_x2 = kwargs.get("noise_x2", 0)
        self.noise_d2 = kwargs.get("noise_d2", 0)

        self.fake_sleep_m1 = kwargs.get("fake_sleep_m1", 0)
        
        self.mirror_1 = Mirror("Mirror 1", self.x1, self.a1, self.d1
                               noise_position=self.noise_x1,
                               noise_pitch=self.noise_a1,
                               fake_sleep=self.fake_sleep_m1)
        self.yag_1 = YAG()

 

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
    def __init__(self, name, initial_position, initial_pitch, z,
                 noise_position=None, noise_pitch=None, fake_sleep=0):

        def position(x):
            if noise_position:
                x += np.random.uniform(-1, 1)*noise_position
            return x
        
        def pitch(alpha):
            if noise_pitch:
                alpha += np.random.uniform(-1, 1)*noise_pitch
            return alpha

        # What here goes into the ordereddict and what is just a regular dict?
        super().__init__(name, OrderedDict([('motor', position),
                                            ('pitch', pitch),
                                            ('motor_setpoint', lambda x : x)]),
                         {'x' : initial_position, 'alpha', : initial_pitch, 
                          'z' : z}, fake_sleep=fake_sleep)

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
    pixel_size = 7.4 #microns
    def __init__(self, name, motor, motor_field,
                 distance, inverted=False,
                 noise_multiplier=None, **kwargs):

        def func():
            #Calculate pixel
            m   = motor.read()[motor_field]['value']
            pos = 2e-6*distance*m/self.pixel_size

            #Add noise
            if noise_multiplier:
                pos += np.random.uniform(-1, 1)*noise_multiplier

            #Invert if reflected image
            if inverted:
                pos = -pos

            return pos

        super().__init__(name, {'centroid': func}, **kwargs)
