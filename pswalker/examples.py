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

class Mirror(Mover):
    """
    Simulation of the Flat Mirror Pitch

    Parameters
    ----------
    name : string
        Name of motor

    initial_set : float
        Initial position of motor in microradians

    noise_multiplier : float, optional
        Scaler to multiply uniform noise 

    fake_sleep, float, optional
        Simulate moving time
    """
    def __init__(self, name, initial_set, noise_multiplier=None, fake_sleep=0):

        def position(x):
            if noise_multiplier:
                x += np.random.uniform(-1, 1)*noise_multiplier
            return x

        super().__init__(name, OrderedDict([('motor', position),
                                            ('motor_setpoint', lambda x : x)]),
                         {'x' : initial_set}, fake_sleep=fake_sleep)

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
