"""
Bluesky Plans for the Walker
"""
############
# Standard #
############
import time
import itertools
import logging
from collections import Iterable
from copy import copy
import logging
###############
# Third Party #
###############
import numpy as np
import bluesky
from scipy.stats   import linregress
from ophyd import Device, Signal
from bluesky.utils import Msg
from bluesky.plans import mv, trigger_and_read, run_decorator, stage_decorator

##########
# Module #
##########
from .examples import TestBase

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
    logger.debug("Running measure_average.")
    logger.debug("Arguments passed: detectors: {0}, target_fields: {1}, num: {2}, \
delay: {3}".format([d.name for d in detectors], target_fields, num, delay))
    #Data structure
    # import ipdb; ipdb.set_trace()
    num = num or 1
    measurements = np.zeros((num, len(target_fields)))

    #Handle delays
    if not isinstance(delay, Iterable):
        delay = itertools.repeat(delay)

    else:
        try:
            num_delays = len(delay)
        except TypeError as err:
            err_msg = "Supplied delay must be scalar or iterable"
            logger.error(err_msg)
            raise ValueError(err_msg) from err

        else:
            if num -1 > num_delays:
                err = "num={:} but delays only provides {:} entires".format(
                    num, num_delays)
                logger.error(err, stack_info=True)                
                raise ValueError(err)
        delay = iter(delay)

    # Expand fields with device names if from ophyd
    target_fields = copy(target_fields)
    for i, (det, fld) in list(enumerate(zip(detectors, target_fields))):
        if isinstance(det, (Device, TestBase)) and det.name not in fld:
            target_fields[i] = "{}_{}".format(det.name, fld)
        elif isinstance(det, Signal):
            target_fields[i] = det.name

    #Gather shots
    logger.debug("Gathering shots..")
    for i in range(num):
        now = time.time()
        #Trigger detector and wait for completion
        for det in detectors:
            yield Msg('trigger', det, group='B')
        #Wait for completion
        yield Msg('wait', None, 'B')
        #Read outputs
        yield Msg('create', None, name='primary')
        det_reads = []
        for det in detectors:
            cur_det = yield Msg('read', det)
            det_reads.append(cur_det)
        for j, det in enumerate(det_reads):
            #Gather average measurements for supplied target_fields
            try:
                measurements[i][j] = det[target_fields[j]]['value']
            except IndexError:
                break
        yield Msg('save')
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
                err = "num={:} but delays only provides {:} entires".format(
                    num, i)
                logger.error(err, stack_info=True)                
                raise ValueError(err)
        #If we have a delay
        if d is not None:
            d = d - (time.time() - now)
            if d > 0:
                yield Msg('sleep', None, d)

    #Return average
    #result = tuple(np.mean(measurements, axis=0))
    result = tuple(np.median(measurements, axis=0))
    logger.debug("Result: {0}".format(result))
    return result


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
    # import ipdb; ipdb.set_trace()
    logger.debug("Running measure_centroid.") 
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
    # import ipdb; ipdb.set_trace()
    logger.debug("Running walk_to_pixel.")
    logger.debug("Arguments passed: detector: {0}, motor: {1}, target: {2}, \
start: {3}, gradient: {4}, target_fields: {5}, first_step: {6}, \
tolerance: {7}, system: {8}, average: {9}, delay: {10}, \
max_steps:{11}".format(detector.name, motor.name, target, start, gradient, 
                       target_fields, first_step, tolerance, system, average, 
                       delay, max_steps))
    system  = system or []
    if start is None:
        start = motor.position

    def walk():
        #Initial measurement
        #logger.debug('walk_to_pixel moving %s to start pos %s', motor, start)
        #yield from mv(motor, start)
        #Take average of motor position and centroid
        (center, pos) = yield from measure_average([detector, motor] + system,
                                                    target_fields,
                                                    num=average, delay=delay)
        def get_first_step(start=start, first_step=first_step, gradient=gradient):
            #Calculate next move if gradient is given
            if gradient:
                intercept = center - gradient*pos
                next_pos = (target - intercept)/gradient
                first_step = next_pos - start

            #Otherwise go with first_step
            else:
                next_pos = start + first_step

            return next_pos
        next_pos = get_first_step(first_step=first_step, gradient=gradient)

        #Store information as we scan
        step = 0
        slope = 0 #WHAT IF WE ARE ALREADY THERE!!!
        centers, angles = [center], [pos]
        #Stop when motors have entered acceptable region
        while not np.isclose(target, center, atol=tolerance):
            #Check we haven't exceed step limit
            if max_steps and step > max_steps:
                break
            logger.debug("Running step {0}...".format(step))
            #Set checkpoint for rewinding
            yield Msg('checkpoint')
            #Move pitch
            logger.debug('walk_to_pixel moving %s to next pos %s', motor,
                         next_pos)
            yield from  mv(motor, next_pos)
            #Measure centroid
            (center, pos) = yield from measure_average(
                                                    [detector, motor] + system,
                                                    target_fields,
                                                    num=average, delay=delay)
            #Store data point
            centers.append(center)
            angles.append(pos)
            #Calculate next step
            logger.debug('calc linregress with angles=%s, centers=%s',
                         angles, centers)
            slope, intercept, r, p, err = linregress(angles, centers)
            logger.debug('linregress: slope=%s, intercept=%s, r=%s, p=%s, err=%s',
                         slope, intercept, r, p, err)
            #Don't divide by zero
            if slope and abs(r) > 0.5:
                next_pos = (target - intercept)/slope
            else:
                logger.warning('linregress was bad, dumping our points')
                next_pos = get_first_step(start=pos,
                                          first_step=first_step,
                                          gradient=gradient)
                step = 0
                centers, angles = [center], [pos]
            step += 1

        logger.debug("Result: {0}".format(center))
        print("Found gradient of {}".format(slope))
        logger.debug("Found gradient of {}".format(slope))
        return center

    return (yield from walk())

