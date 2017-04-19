"""
Bluesky Plans for the Walker
"""
############
# Standard #
############

###############
# Third Party #
###############
import numpy as np
import bluesky
from bluesky.utils import Msg
from bluesky.plans import trigger_and_read, run_decorator, stage_decorator

##########
# Module #
##########


def walk_to_pixel(detector, motor, target,
                  start, min_step=0.00001,
                  inverted=False,
                  tolerance=20, average=None,
                  md=None):
    """
    Step a motor until a specific threshold is reached on the detector
    
    Parameters
    ----------
    detector : :class:`.BeamDetector`
        YAG to make measure beam centroid

    motor : :class:`.FlatMirror`
        Mirror to adjust pitch mechanism

    target : int
        Target pixel for beam centroid

    start : float
        Starting position for pitch mechanism

    min_step : float
        Step size between successive centroid checks

    inverted : bool, optional
        Whether the imager is viewing a reflected YAG screen or a direct imager 

    tolerance : int, optional
        Number of pixels the final centroid position is allowed to differ from
        the target

    average : int, optional
        Number of images to average together for each step along the scan

    md : dict, optional
        metadata
    """
    ######################################
    #Error handling still needs to be done
    #
    #Too large a step size
    #Impossible target
    ######################################

    #Average
    shots_per_step = average or 1

    #Assemble metadata
    _md = {'detectors'      : [det.name],
           'motors'         : [motor.name],
           'target'         : target,
           'shots_per_step' : shots_per_step,
           'min_step'       : min_step,
           'plan_name'      : 'walk_to_pixel'}
    _md.update(md or {})

    #Centroid measurement
    def measure_centroid():
        centers = np.zeros(shots_per_step)
        #Gather shots
        for i, shot in enumerate(shots_per_step):
            centers[i] = yield from trigger_and_read(detector)

        #Return average
        return np.mean(shot['centroid']['value'] for shot in centers)
           

    @run_decorator(md=_md)
    @stage_decorator([detector, motor])
    def walk():
        #Initial measurement
        center   = yield from measure_centroid()

        next_pos = start
        #Stop when motors have entered acceptable region
        while not np.isclose(target, center, atol=tolerance):
            #Set checkpoint for rewinding
            yield Msg('checkpoint')
            #Move pitch
            yield from mv(motor, next_pos)
            #Meausre centroid
            center   = yield from measure_centroid()
            #Calculate next step
            next_pos += np.sign(target-center)*min_step
            #If we are looking at a reflected image, flip sign
            if inverted:
                next_pos = -next_pos

    return (yield from walk())


