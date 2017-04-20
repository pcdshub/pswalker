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
from scipy.stats   import linregress
from bluesky.utils import Msg
from bluesky.plans import mv, trigger_and_read, run_decorator, stage_decorator

##########
# Module #
##########

def measure_centroid(detector, average=None, md=None):
    """
    Measure the centroid of the beam on a YAG screen

    Parameters
    ----------
    detector : :class:`.BeamDetector`
        YAG to make measure beam centroid

    average : int, optional
        Number of images to average together for each step along the scan

    md : dict, optional
        metadata

    Returns
    -------
    centroid : tuple
        Position of the center, averaged over any number of shots
    """
    #Gather metadata
    nshots  = average or 1
    centers = np.zeros(nshots)
    _md = {'detectors' : [det.name],
           'nshots'    : nshots,
           'plan_name' : 'measure_centroid'}
    _md.update(md or {})

    #Gather shots
    for i, shot in enumerate(nshots):
        centers[i] = yield from trigger_and_read(detector)

    #Return average
    return np.mean(shot['centroid']['value'] for shot in centers)


def walk_to_pixel(detector, motor, target,
                  start, first_step=1e-3,
                  tolerance=20, average=None,
                  md=None):
    """
    Step a motor until a specific threshold is reached on the detector

    This function assumes a linear relationship between the position of the
    given motor and the position on the YAG. While at the onset of the plan, we
    don't know anything about the physical setup of the system, we can track
    the steps as they happen and use our prior attempts to inform future ones.

    The first step of the plan takes a naive step out into the unknown
    parameter space of the model. Using the two data points of the initial
    centroid and the result of our first step we can form a coarse model by
    simply drawing a line through each point. A new step is calculated based on
    this rudimentary model, and the centroid is measured again now at a third
    point. As we gather more data points on successive attempts at alignment
    our linear fit improves. The iteration stops when the algorithm has
    centered the beam within the specified tolerance

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

    first_step : float, optional
        Initial step to attempt

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
    #Impossible target
    #Too large initial step
    #No beam on PIM
    ######################################

    #Assemble metadata
    _md = {'detectors' : [det.name],
           'motors'    : [motor.name],
           'target'    : target,
           'min_step'  : min_step,
           'tolerance' : tolerance,
           'plan_name' : 'walk_to_pixel'}
    _md.update(md or {})

    def walk():
        #Initial measurement
        yield from mv(motor, start)
        center = yield from measure_centroid(detector, average=averaage)
        #Store information as we scan
        next_pos = start + first_step
        centers, angles = [center], [angles]

        #Stop when motors have entered acceptable region
        while not np.isclose(target, center, atol=tolerance):

            #Set checkpoint for rewinding
            yield Msg('checkpoint')
            #Move pitch
            yield from mv(motor, next_pos)
            #Measure centroid
            center = yield from measure_centroid(detector, average=average)

            #Store data point
            centers.append(center)
            angles.append(next_pos)
            #Calculate next step
            slope, intercept, r, p, err = linregress(angles, centers)
            next_step = (target - intercept)/slope

    return (yield from walk())


