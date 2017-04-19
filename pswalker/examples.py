"""
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
from bluesky.examples import Mover, Reader

##########
# Module #
##########

logger = logging.getLogger(__name__)


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
        Name of motor_field to calculate centroid position

    distance : float
        Distance from mirror to YAG

    inverted : bool, optional
        Whether the image is reflected before being imaged by the camera

    noise_multiplier : float, optional
        Introduce unifrom random noise to the pixel location
    """
    pixel_size = 7.4e-6
    def __init__(self, name, motor, motor_field,
                 distance, inverted=False,
                 noise_multiplier=None, **kwargs):

        def func():
            #Calculate pixel
            m   = motor.read()[motor_field]['value']
            pos = distance*m/self.pixel_size

            #Add noise
            if noise_multiplier:
                pos += np.random.uniform(-1, 1)*noise_multiplier
            
            #Invert if reflected image
            if inverted:
                pos = -pos

            return pos

        super().__init__(name, {'centroid': func}, **kwargs)
