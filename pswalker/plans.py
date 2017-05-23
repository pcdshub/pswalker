"""
Bluesky Plans for the Walker
"""
############
# Standard #
############
import time
import itertools
from collections import Iterable
import logging
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

logger = logging.getLogger(__name__)

#TODO Half assed generalization, should really use count but it has those pesky
#     run/stage decorators

def measure_average(detectors, target_fields, num=1, delay=None):
    """
    Gather a series of measurements from a list of detectors and return the
    average over the number of shots

    Parameters
    ----------
    detector : list
        YAG to make measure beam centroid

    target_fields : list
        Fields to average for each detector. If a detector is not supplied
        target_field, a meausurement is taken at each step, however, the
        average won't be included in the final tuple

    num : int, optional
        Number of samples to average together for each step along the scan

    delay : iterable or scalar, optional
        Time delay between successive readings

    Returns
    -------
    average : tuple
        Tuple of the average over each event for each target_field
    """
    #Data structure
    measurements = np.zeros((num, len(target_fields)))

    #Handle delays
    if not isinstance(delay, Iterable):
        delay = itertools.repeat(delay)

    else:
        try:
            num_delays = len(delay)

        except TypeError:
            raise ValueError("Supplied delay must be scalar or iterable")

        else:
            if num -1 > num_delays:
                raise ValueError("num={:} but delays only provides {:} "
                                 "entires".format(num, num_delays))
        delay = iter(delay)

    #Gather shots
    for i in range(num):
        now = time.time()
        #Trigger detector and wait for completion
        for det in detectors:
            yield Msg('trigger', det, group='B')
        #Wait for completion
        yield Msg('wait', None, 'B')
        #Read outputs
        for j, det in enumerate(detectors):
            yield Msg('create', None, name='primary')
            cur_det = yield Msg('read', det)
            yield Msg('save')
            #Gather average measurements for supplied target_fields
            try:
                measurements[i][j] = cur_det[target_fields[j]]['value']
            except IndexError:
                break
        #Delay before next reading 
        try:
            d = next(delay)
        #Out of delays
        except StopIteration:
            #If our last measurement that is fine
            if i +1 == num:
                break
            #Otherwise raise exception
            else:
                raise ValueError("num={:} but delays only provides {:} "
                                 "entires".format(num, i))
        #If we have a delay
        if d is not None:
            d = d - (time.time() - now)
            if d > 0:
                yield Msg('sleep', None, d)

    #Return average
    return tuple(np.mean(measurements, axis=0))


def measure_centroid(det, target_field='centroid_x',
                     average=None, delay=None):
    """
    Measure the centroid of the beam over one or more images

    Parameters
    ----------
    det : :class:`.BeamDetector`
        `readable` object

    target_field : str
        Name of attribute associated with centroid position

    average : int, optional
        Number of shots to average centroid position over

    delay : float, optional
        Time to wait inbetween images
    """
    return measure_average([det],[target_field],
                            num=average, delay=delay)


def walk_to_pixel(detector, motor, target,
                  start=None, gradient=None,
                  target_fields=['centroid_x', 'alpha'],
                  first_step=1., tolerance=20, system=None,
                  average=None, delay=None, max_steps=None):
    """
    Step a motor until a specific threshold is reached on the detector

    This function assumes a linear relationship between the position of the
    given motor and the position on the YAG. While at the onset of the plan, we
    don't know anything about the physical setup of the system, we can track
    the steps as they happen and use our prior attempts to inform future ones.

    The first step of the plan makes a move out into the unknown parameter
    space of the model. Using the two data points of the initial centroid and
    the result of our first step we can form a coarse model by simply drawing a
    line through each point. A new step is calculated based on this rudimentary
    model, and the centroid is measured again now at a third point. As we
    gather more data points on successive attempts at alignment our linear fit
    improves. The iteration stops when the algorithm has centered the beam
    within the specified tolerance.

    There are ways to seed the walk with the known information to make the
    first step the algorithm takes more fruitful. The most naive is to give it
    a logical first step size that will keep the object you are trying to
    center within the image. However, in some cases we may know enough to have
    a reasonable first guess at the relationship between pitch and centroid. In
    this case the algorithm accepts the :param:`.gradient` parameter that is
    then used to calculate the optimal first step. 

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

    gradient : float, optional
        Assume an initial gradient for the relationship between pitch and beam
        center

    target_fields : iterable, optional
        (detector, motor) fields to average and calculate line of best fit

    system : list, optional
        Extra detectors to include in the datastream as we measure the average

    tolerance : int, optional
        Number of pixels the final centroid position is allowed to differ from
        the target

    average : int, optional
        Number of images to average together for each step along the scan

    max_steps : int, optional
        Limit the number of steps the walk will take before exiting
    """
    ######################################
    #Error handling still needs to be done
    #
    #Impossible target
    #Too large initial step
    #No beam on PIM
    ######################################
    average = average or 1
    system  = system or []
    if start is None:
        start = motor.position

    def walk():
        #Initial measurement
        yield from mv(motor, start)
        #Take average of motor position and centroid
        (center, pos) = yield from measure_average([detector, motor]+system,
                                                    target_fields,
                                                    num=average, delay=delay)
        #Calculate next move if gradient is given
        if gradient:
            intercept = center - gradient*pos
            next_pos = (target - intercept)/gradient
        #Otherwise go with first_step
        else:
            next_pos = start + first_step
        #Store information as we scan
        step = 0
        centers, angles = [center], [pos]
        #Stop when motors have entered acceptable region
        while not np.isclose(target, center, atol=tolerance):
            #Check we haven't exceed step limit
            if max_steps and step > max_steps:
                break
            #Set checkpoint for rewinding
            yield Msg('checkpoint')
            #Move pitch
            yield from  mv(motor, next_pos)
            #Measure centroid
            (center, pos) = yield from measure_average(
                                                    [detector, motor],
                                                    target_fields,
                                                    num=average, delay=delay)
            #Store data point
            centers.append(center)
            angles.append(next_pos)
            #Calculate next step
            slope, intercept, r, p, err = linregress(angles, centers)
            #Don't divide by zero
            if slope:
                next_pos = (target - intercept)/slope
            step += 1

        return center

    return (yield from walk())


