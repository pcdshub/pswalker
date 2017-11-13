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
###############
# Third Party #
###############
import numpy as np
import pandas as pd
import bluesky
from scipy.stats   import linregress
from ophyd import Device, Signal
from bluesky.utils import Msg
from bluesky.plan_stubs import mv, rel_set, trigger_and_read
from bluesky.preprocessors import run_decorator, stage_decorator

##########
# Module #
##########
from .callbacks import LinearFit, apply_filters, rank_models
from .utils import field_prepend
from .utils.exceptions import FilterCountError

logger = logging.getLogger(__name__)

def measure_average(detectors, num=1, filters=None,
                    delay=None, drop_missing=True):
    """
    Gather a series of measurements from a list of detectors and return the
    average over the number of shots.
    Parameters
    ----------
    detectors : list
        List of detectors to measure at each event

    num : int, optional
        Number of samples to average together for each step along the scan

    delay : iterable or scalar, optional
        Time delay between successive readings

    Returns
    -------
    average : dict
        A dictionary of all the measurements taken from the supplied detectors
        averaged over `num` shots. In the event that a field is a string, or
        can not be averaged the last shot is returned

    See Also
    --------
    :func:`.measure`
    """
    #Gather data
    data = yield from measure(detectors, num=num, delay=delay,
                              filters=filters, drop_missing=drop_missing)

    #Gather keys
    avg = dict.fromkeys(set([key for d in data for key in d.keys()]))
    for key in avg.keys():
        try:
            avg[key] = np.mean([d[key] for d in data])
        except TypeError:
            avg[key] = data[-1][key]

    logger.debug("Found the following averages: %s", avg)
    return avg


def measure_centroid(det, target_field='centroid_x',
                     average=1, delay=None, filters=None,
                     drop_missing=True):
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
    logger.debug("Running measure_centroid.") 
    #Use default filters
    filters = filters or {field_prepend(target_field, det) : lambda x : x > 0}
    #Take average measurement
    avgs = yield from measure_average([det], num=average, delay=delay,
                                       filters=filters, drop_missing=drop_missing)
    return avgs[field_prepend(target_field, det)]


def walk_to_pixel(detector, motor, target, filters=None,
                  start=None, gradient=None, models=[],
                  target_fields=['centroid_x', 'alpha'],
                  first_step=1., tolerance=20, system=None,
                  average=1, delay=None, max_steps=None,
                  drop_missing=True):
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
    this case the algorithm accepts the ``gradient`` parameter that is then
    used to calculate the optimal first step. 

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

    models : list, optional
        Additional models to include in the :func:`.fitwalk`

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
    #Prepend field names
    target_fields = [field_prepend(fld, obj)
                     for (fld, obj) in zip(target_fields,[detector, motor])]

    system  = system or list()
    average = average or 1
    #Travel to starting position
    if start:
        yield from mv(motor, start)

    else:
        start = motor.position

    #Create initial step plan
    if gradient:
        #Seed the fit with our estimate
        init_guess = {'slope' : gradient}
        #Take a quick measurement
        def gradient_step():
            logger.debug("Using gradient of {} for naive step..."
                        "".format(gradient))
            #Take a quick measurement 
            avgs = yield from measure_average([detector, motor] + system,
                                               filters=filters,
                                               num=average, delay=delay,
                                               drop_missing=drop_missing)
            #Extract centroid and position
            center, pos = avgs[target_fields[0]], avgs[target_fields[1]]
            #Calculate corresponding intercept
            intercept = center - gradient*pos
            #Calculate best step on first guess of line
            next_pos = (target - intercept)/gradient
            logger.debug("Predicting position using line y = {}*x + {}"
                         "".format(gradient, intercept))
            #Move to position
            yield from mv(motor, next_pos)

        naive_step = gradient_step
    else:
        init_guess = dict()
        def naive_step():
            return (yield from rel_set(motor, first_step, wait=True))

    #Create fitting callback
    fit = LinearFit(target_fields[0], target_fields[1],
                    init_guess=init_guess, average=average,
                    name='Linear')

    #Fitwalk
    last_shot, accurate_model = yield from fitwalk([detector]+system, motor, [fit]+models, target,
                                        naive_step=naive_step, average=average,
                                        filters=filters, tolerance=tolerance, delay=delay,
                                        drop_missing=drop_missing, max_steps=max_steps)
    
    #Report if we did not need a model
    if not accurate_model:
        logger.debug("Reached target without use of model")

    return last_shot, accurate_model


def measure(detectors, num=1, delay=None, filters=None, drop_missing=True,
            max_dropped=50):
    """
    Gather a fixed number of measurements from a group of detectors

    Parameters
    ----------
    detectors : list
        List of detector objects to read and bundle

    num : int
        Number of measurements that pass filters

    delay : float
        Minimum time between consecutive reads of the detectors.

    filters : dict, optional
        Key, callable pairs of event keys and single input functions that
        evaluate to True or False. For more infromation see
        :meth:`.apply_filters`

    drop_missing : bool, optional
        Choice to include events where event keys are missing

    max_dropped : int, optional
    	Maximum number of events to drop before raising a ValueError

    Returns
    -------
    data : list
        List of mock-event documents
    """
    #Log setup
    logger.debug("Running measure")
    logger.debug("Arguments passed: detectors: {0}, "\
                 "num: {1}, delay: {2}, drop_missing: {3}"\
                 "".format([d.name for d in detectors],
                           num, delay,drop_missing))

    #If scalable, repeat forever
    if not isinstance(delay, Iterable):
        delay = itertools.repeat(delay)

    else:
        #Number of supplied delays
        try:
            num_delays = len(delay)

        #Invalid delay
        except TypeError as err:
            err_msg = "Supplied delay must be scalar or iterable"
            logger.error(err_msg)
            raise ValueError(err_msg) from err

        #Handle provided iterable
        else:
            #Invalid number of delays for shot counts
            if num -1 > num_delays:
                err = "num={:} but delays only provides "\
                      "{:} entries".format(num, num_delays)
                logger.error(err, stack_info=True)
                raise ValueError(err)
        #Ensure it is an iterable
        delay = iter(delay)

    #Gather shots
    logger.debug("Gathering shots..")
    shots   = 0
    dropped = 0
    data    = list()
    filters = filters or dict()
    #Gather fixed number of shots
    while shots < num:
        #Timestamp earliest possible moment
        now = time.time()

        #Trigger detector and wait for completion
        for det in detectors:
            yield Msg('trigger', det, group='B')

        #Wait for completion and start bundling
        yield Msg('wait',   None, 'B')
        yield Msg('create', None, name='primary')

        #Mock-event document
        det_reads = dict()

        #Gather shots
        for det in detectors:
            cur_det = yield Msg('read', det)
            det_reads.update(dict([(k,v['value'])
                             for k,v in cur_det.items()]))
        #Emit Event doc to callbacks
        yield Msg('save')

        #Apply filters
        unfiltered = apply_filters(det_reads, filters=filters, drop_missing=drop_missing)
        #Increment shots if filters are passed
        shots += int(unfiltered)
        #Do not delay if we have not passed filter
        if unfiltered:
            #Append recent read to data list
            data.append(det_reads)

            #Gather next delay
            try:
                d = next(delay)

            #Out of delays
            except StopIteration:
                #If our last measurement that is fine
                if shots == num:
                    break
                #Otherwise raise exception
                else:
                    err = "num={:} but delays only provides {:} entries".format(
                        num, shots)
                    logger.error(err, stack_info=True)
                    raise ValueError(err)

            #If we have a delay, sleep
            if d is not None:
                d = d - (time.time() - now)
                if d > 0:
                    yield Msg('sleep', None, d)

        #Report filtered event
        else:
            dropped += 1
            logger.debug('Ignoring inadequate measurement, '\
                         'attempting to gather again...')
        if dropped > max_dropped:
            dropped_dict = {}
            for key in filters.keys():
                dropped_dict[key] = det_reads[key]
            logger.debug(('Dropped too many events, raising exception. Latest '
                          'bad values were %s'), dropped_dict)
            raise FilterCountError
    #Report finished
    logger.debug("Finished taking {} measurements, "\
                 "filters removed {} events"\
                 "".format(len(data), dropped))

    return data


def fitwalk(detectors, motor, models, target,
            naive_step=None, average=120,
            filters=None, drop_missing=True,
            tolerance=10, delay=None, max_steps=10):
    """
    Parameters
    ----------
    detectors : list
        List of detectors to read at each step of walk

    motor : ``ophyd.Object``
        Ophyd object that supports the set and wait. This should have a one to
        one relationship with the independent variable in the model you plan to
        optimize

    models : list
        List of models to evaluate during the walk

    target : float
        Desired end position for the walk

    naive_step : bluesky.plan, optional
        Plan to execute when there is not an accurate enough model available.
        By default this is ``mv(0.01)``

    average : int, optional
        Number of readings to take and average at each event. Models are
        allowed to take a subset of each reading and average, however if the
        two settings will create an average over multiple steps in the walk the
        :attr:`.LiveBuild.average` setting is automatically updated. For
        example, if the walk is told to average over 10 events, your model can
        either average over 10, 5, 2, or 1 shots.

    filters : dict, optional
        Key, callable pairs of event keys and single input functions that
        evaluate to True or False. For more infromation see
        :meth:`.apply_filters`

    drop_missing : bool, optional
        Choice to include events where event keys are missing

    tolerance : float, optional
        Maximum distance from target considered successful

    delay : float, optional
        Mininum time between consecutive readings

    max_steps : int, optional
        Maximum number of steps the scan will attempt before faulting.
        There is a max of 10 by default, but you may disable this by setting
        this option to None. Note that this may cause the walk to run indefinitely.
    """
    #Check all models are fitting the same key
    if len(set([model.y for model in models])) > 1:
        raise RuntimeError("Provided models must predict "\
                           "the same dependent variable.")
    #Prepare model callbacks
    for model in models:
        #Modify averaging
        if average % model.average != 0:
            logger.warning("Model {} was set to an incompatible averaging "
                           "setting, changing setting to {}".format(model.name,
                                                                    average))
            model.average = average
        #Subscribe callbacks
        yield Msg('subscribe', None, model, 'all')

    #Target field
    target_field = models[0].y

    #Install filters
    filters = filters or {}
    [m.install_filters(filters) for m in models]

    #Link motor to independent variables
    detectors.insert(1, motor)
    field_names = list(set(var for model in models
                           for var in model.independent_vars.values()))
    motors  = dict((key, motor) for key in field_names
                    if key in motor.read_attrs)

    #Initialize variables
    steps      = 0
    if not naive_step:
        def naive_step():
            return (yield from rel_set(motor, 0.01, wait=True))

    #Measurement method
    def model_measure():
        #Take average measurement
        avg = yield from measure_average(detectors,
                                         num=average, delay=delay,
                                         drop_missing=drop_missing,
                                         filters=filters)
        #Save current target position
        last_shot = avg.pop(target_field)
        logger.debug("Averaged data yielded {} is at {}"
                     "".format(target_field, last_shot))

        #Rank models based on accuracy of fit
        model_ranking = rank_models(models, last_shot, **avg)

        #Determine if any models are accurate enough
        if len(model_ranking):
            model = model_ranking[0]

        else:
            model = None

        return avg, last_shot, model

    #Make first measurements
    averaged_data, last_shot, accurate_model = yield from model_measure()
    #Begin walk
    while not np.isclose(last_shot, target, atol=tolerance):
        #Log error
        if not steps:
            logger.debug("Initial error before fitwalk is {}"
                         "".format(int(target-last_shot)))
        else:
            logger.debug("fitwalk is reporting an error {} of after step #{}"\
                         "".format(int(target-last_shot), steps))
        #Break on maximum step count
        if max_steps and steps >= max_steps:
            raise RuntimeError("fitwalk failed to converge after {} steps"\
                               "".format(steps))

        #Use naive step plan if no model is accurate enough
        #or we have not made a step yet
        if not accurate_model or steps==0:
            logger.debug("No model yielded accurate prediction, "\
                         "using naive plan")
            yield from naive_step()
        else:
            logger.debug("Using model {} to determine next step."\
                        "".format(accurate_model.name))
            #Calculate estimate of next step from accurate model
            fixed_motors = dict((key, averaged_data[key])
                                 for key in field_names
                                 if key not in motors.keys())

            #Try and step off model prediction
            try:
                estimates = accurate_model.backsolve(target, **fixed_motors)

            #Report model faults
            except Exception as e:
                logger.warning("Accurate model {} was unable to backsolve "
                               "for target {}".format(accurate_model.name,
                                                      target))
                logger.warning(e)

                #Reuse naive step
                logger.debug("Reusing naive step due to lack of accurate model")
                yield from naive_step()
            else:
                #Move system to match estimate
                for param, pos in estimates.items():
                    #Watch for NaN
                    if pd.isnull(pos) or np.isinf(pos):
                        raise RuntimeError("Invalid position return by fit")
                    #Attempt to move
                    try:
                        logger.debug("Adjusting motor {} to position {:.1f}"\
                                     "".format(motor.name, pos))
                        yield from mv(motor, pos)

                    except KeyboardInterrupt as e:
                        logger.debug("No motor found to adjust variable {}"\
                                     "".format(e))
        #Count our steps
        steps += 1

        #Take a new measurement
        logger.debug("Resampling after successfull move")
        averaged_data, last_shot, accurate_model = yield from model_measure()

    #Report a succesfull run
    logger.info("Succesfully walked to value {} (target={}) after {} steps."\
                "".format(int(last_shot), target, steps))

    return last_shot, accurate_model
