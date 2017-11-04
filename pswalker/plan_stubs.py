#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import threading
import uuid
import logging

from bluesky.plan_stubs import wait as plan_wait, abs_set, create, read, save
from bluesky.preprocessors import stage_wrapper
from bluesky.utils import FailedStatus

from .plans import measure_average
from .utils.argutils import as_list, field_prepend
from .utils.exceptions import BeamNotFoundError
from math import nan, isnan
from functools import partial

logger = logging.getLogger(__name__)


def prep_img_motors(n_mot, img_motors, prev_out=True, tail_in=True,
                    timeout=None):
    """
    Plan to prepare image motors for taking data. Moves the correct imagers in
    and waits for them to be ready.

    Parameters
    ----------
    n_mot: int
        Index of the motor in img_motors that we need to take data with.

    img_motors: list of OphydObject
        OphydObjects to move in or out. These objects need to have .set methods
        that accept the strings "IN" and "OUT", reacting appropriately, and
        need to accept a "timeout" kwarg that allows their status to be set as
        done after a timeout. These should be ordered by increasing distance
        to the source.

    prev_out: bool, optional
        If True, pull out imagers closer to the source than the one we need to
        use. Default True. (True if imager blocks beam)

    tail_in: bool, optional
        If True, put in imagers after this one, to be ready for later. If
        False, don't touch them. We won't wait for the tail motors to move in.

    timeout: number, optional
        Only wait for this many seconds before moving on.

    Returns
    -------
    ok: bool
        True if the wait succeeded, False otherwise.
    """
    start_time = time.time()

    prev_img_mot = str(uuid.uuid4())
    ok = True

    try:
        for i, mot in enumerate(img_motors):
            if i < n_mot and prev_out:
                if timeout is None:
                    yield from abs_set(mot, "OUT", group=prev_img_mot)
                else:
                    yield from abs_set(mot, "OUT", group=prev_img_mot,
                                       timeout=timeout)
            elif i == n_mot:
                if timeout is None:
                    yield from abs_set(mot, "IN", group=prev_img_mot)
                else:
                    yield from abs_set(mot, "IN", group=prev_img_mot,
                                       timeout=timeout)
            elif tail_in:
                yield from abs_set(mot, "IN")
        yield from plan_wait(group=prev_img_mot)
    except FailedStatus:
        ok = False

    if ok and timeout is not None:
        ok = time.time() - start_time < timeout

    if ok:
        logger.debug("prep_img_motors completed successfully")
    else:
        logger.debug("prep_img_motors exitted with timeout")
    return ok


def match_condition(signal, condition, mover, setpoint, timeout=None,
                    sub_type=None, has_stop=True):
    """
    Plan to adjust mover until condition(signal.value) returns True.

    Parameters
    ----------
    signal: Signal
        Object that implements the Bluesky "readable" interface, including the
        optional subscribe function, sending at least the keyword "value" as in
        ophyd.Signal.

    condition: function
        Function that accepts a single argument, "value", and returns
        True or False.

    mover: Device
        Object that implements both the Bluesky "readable" and "movable"
        interfaces, accepting "moved_cb" as a keyword argument as in
        ophyd.positioner.PositionerBase.

    setpoint: any
        We will call mover.set(setpoint). Pick a good value (the limit switch?)

    timeout: float, optional
        Stop if we hit a timeout.

    sub_type: str, optional
        Use a different subscription than the signal's default.

    has_stop: bool, optional
        Boolean to indicate whether or not we can stop the motor. We usually
        use the motor's stop command to stop at the signal. If this is set to
        False (e.g. we can't stop it), go back to center of the largest range
        with the condition satisfied after reaching the end.

    Returns
    -------
    ok: bool
        True if we reached the condition, False if we timed out or reached the
        setpoint before satisfying the condition.
    """
    # done = threading.Event()
    success = threading.Event()

    if has_stop:
        def condition_cb(*args, value, **kwargs):
            if condition(value):
                success.set()
                mover.stop()
    else:
        pts = []

        def condition_cb(*args, value, **kwargs):
            nonlocal pts
            if condition(value):
                pts.append((mover.position, True))
            else:
                pts.append((mover.position, False))

    if sub_type is not None:
        signal.subscribe(condition_cb, sub_type=sub_type)
    else:
        signal.subscribe(condition_cb)

    try:
        yield from abs_set(mover, setpoint, wait=True, timeout=timeout)
    except FailedStatus:
        logger.warning("Timeout on motor %s", mover)

    if not has_stop:
        best_start = -1
        best_end = -1
        curr_start = -1
        curr_end = -1

        def new_best(best_start, best_end, curr_start, curr_end):
            if -1 in (best_start, best_end):
                return curr_start, curr_end
            elif -1 in (curr_start, curr_end):
                return best_start, best_end
            else:
                curr_dist = abs(pts[curr_end][0] - pts[curr_start][0])
                best_dist = abs(pts[best_end][0] - pts[best_start][0])
                if curr_dist > best_dist:
                    return curr_start, curr_end
                else:
                    return best_start, best_end

        logger.debug("Checking a set of %i stored points", len(pts))
        for i, (pos, ok) in enumerate(pts):
            if ok:
                if curr_start == -1:
                    curr_start = i
                curr_end = i
            else:
                best_start, best_end = new_best(best_start, best_end,
                                                curr_start, curr_end)
                curr_start = -1
                curr_end = -1
        best_start, best_end = new_best(best_start, best_end,
                                        curr_start, curr_end)
        if -1 in (best_start, best_end):
            logger.debug('did not find any valid points: %s', pts)
        else:
            logger.debug('found valid points, moving back')
            start = pts[best_start][0]
            end = pts[best_end][0]
            try:
                yield from abs_set(mover, (end+start)/2, wait=True,
                                   timeout=timeout)
            except FailedStatus:
                logger.warning("Timeout on motor %s", mover)
            if condition(signal.value):
                success.set()

    signal.clear_sub(condition_cb)

    ok = success.is_set()
    if ok:
        logger.debug(('condition met in match_condition, '
                      'mover=%s setpt=%s cond value=%s'),
                     mover.name, setpoint, signal.value)
    else:
        logger.debug(('condition fail in match_condition, '
                      'mover=%s setpt=%s cond value=%s'),
                     mover.name, setpoint, signal.value)
    return ok


def slit_scan_area_comp(slits, yag, x_width=1.0,y_width=1.0,samples=1):
    """Find the ratio of real space/pixel in the PIM

    1. Send slits to specified position
    2. Measure pixel dimensions of passed light. 
        The idea is that the width, height values will be pulled from the
        PIMPulnixDetector instance.

    2b. Should diffraction issues (as observed with the test laser) persist
        when using the x-ray laser, another method will be necessary  instead 
        of using the gap dimensions for calibration, we could move the gap in 
        the slits a small distance and observe the position change of the 
        passed light. If the light is highly collimated (it should be), the 
        motion of the gap should be 1:1 with the motion of the passed light on
        the PIM detector. Only investigate if issues persisit in x-ray. 

    Parameters
    ----------
    slits : pcdsdevices.slits.Slits
        Ophyd slits object from pcdsdevices.slits.Slits 
    
    yag : pcdsdevices.sim.pim.PIM (subject to change?)
        Ophyd object of some type, this will allow me to read the w, h 
        (w,h don't exist yet but they should shortly)

    x_width : int 
        Define the target x width of the gap in the slits. Units: mm

    y_width : int 
        Define the target y width of the gap in the slits. Units: mm

    samples : int
        number of sampels to use and average over when measuring width, height


    Returns
    -------
    (float,float)
        returns a tuple of x and y scaling respectively. Units mm/pixels
    """
    # place slits then read a value that doesn't exist yet
    # easy
    # measure_average()
    #data = yield from measure_average([yag],['xwidth','ywidth'])

    # set slits to specified gap size
    yield from abs_set(slits, x=x_width, y=y_width, wait=True)

    # read profile dimensions from image (width plugin pending)
    yag_measurements = yield from measure_average(
        [yag],
        num=samples
    )

    # extract measurements of interest from returned dict
    yag_measured_x_width = yag_measurements[field_prepend('xwidth', yag)]
    yag_measured_y_width = yag_measurements[field_prepend('ywidth', yag)]

    logger.debug("Measured x width: {}".format(yag_measured_x_width))
    logger.debug("Measured y width: {}".format(yag_measured_y_width))

    # err if image not received or image has 0 width,height 
    if (yag_measured_x_width <= 0 \
        or yag_measured_y_width <=0):
        raise ValueError("A measurement less than or equal to zero has been" 
                         "measured. Unable to calibrate")
        x_scaling = nan
        y_scaling = nan
    else:
        #data format: Real space / pixel
        x_scaling = x_width / yag_measured_x_width
        y_scaling = y_width / yag_measured_y_width

    return x_scaling, y_scaling


def slit_scan_fiducialize(slits, yag, x_width=0.01, y_width=0.01,
                          samples=10, filters=None,
                          centroid='detector_stats2_centroid_y'):
    """
    Assists beam alignment by setting the slits to a w,h and checking,
    returning the centroid position.

    Parameters
    ----------
    slits : pcdsdevices.slits.Slits
        Ophyd slits object from pcdsdevices.slits.Slits

    yag : pcdsdevices.pim.PIM
        Detector to fidicuialize. This plan assumes the detector is stated and
        inserted

    x_width : float
        x dimensions of the gap in the slits. EGU: mm

    y_width : float
        y dimensions of the gap in the slits. EGU: mm

    samples : int
        Returned measurements are averages over multiple samples. samples arg
        determines the number of samples to average over for returned data

    filters : dict, optional
        Key, callable pairs of event keys and single input functions that
        evaluate to True or False. For more infromation see
        :meth:`.apply_filters`

    centroid : str, optional
        Key to gather centroid information

    Returns
    -------
    float
        return centroid position in pixel space, single axis
    """
    # Set slits and imager, wait together
    group = str(uuid.uuid4())
    yield from abs_set(yag, "IN", group=group)
    yield from abs_set(slits, x_width, group=group)
    yield from plan_wait(group=group)

    #Collect data from yags
    yag_measurements = yield from measure_average([yag], num=samples,
                                                  filters=filters)

    #Extract centroid positions from yag_measurments dict
    centroid = yag_measurements[field_prepend(centroid, yag)]

    return centroid


def fiducialize(slits, yag, start=0.1, step_size=0.5, max_width=5.0,
                filters=None, centroid='detector_stats2_centroid_y',
                samples=10):
    """
    Fiducialize a detector using upstream slits

    Close the slits to a value specified by `start`. Then measure the centroid
    of the shadow left on the YAG by the upstream slits. If the beam is
    misaligned to the point that closing the slits does not give us a
    measureable beam centroid, we increment the aperature of the slits by
    `step_size`. The scan will stop and return the calculated `fidicuial` when
    it receives a non-zero centroid, raising an `BeamNotFoundError` if the
    slits reach `max_width` without seeing the beam

    Parameters
    ----------
    slits : `pcdsdevices.slits.Slits`
        Upstream slits

    yag : `pcdsdevices.pim.PIM`
        Detector to measure centroid

    start : float, optional
        Initial value to set slit widths

    step_size : float, optional
        Size of each step

    max_width : float, optional
        Maximum allowed slit aperature before raising an Exception

    samples : int, optional
        Number of shots to average over

    filters : dict, optional
        Filters to eliminate shots

    centroid : str, optional
        Field name of centroid measurement

    Returns
    -------
    fiducial : float
        Measured fiducial

    Raises
    ------
    BeamNotFoundError:
        If the requested slit width exceeds `max_width`
    
    Notes
    -----
    This plan makes the following assumptions; the slits are aligned to the
    xrays in their current center positions, the YAG is inserted and the
    areaDetector plugins are configured in such a way to accurately return the
    centroid of the beam
    """
    #Repeatedly take fiducials
    while start < max_width:
        logger.debug("Measuring fiducial with slit {} at {}"
                     "".format(slits.name, start))
        fiducial = yield from slit_scan_fiducialize(slits, yag, x_width=start,
                                                    y_width=start,
                                                    filters=filters,
                                                    centroid=centroid,
                                                    samples=samples)
        #If we got a real fiducial return it
        if fiducial > 0.0:
            logger.info("Found fiducial of {} on {} using {}"
                        "".format(fiducial, yag.name, slits.name))
            return fiducial

        #Increase slit width if we did not get a centroid
        logger.debug("No centroid measurement found, expanding slit aperature")
        start += step_size

    #Next step would exceed max_width
    raise BeamNotFoundError


def homs_fiducialize(slit_set, yag_set, x_width=.01, y_width=.01, samples=10,
                      filters = None, centroid='detector_stats2_centroid_y'): 
    """
    Run slit_scan_fiducialize on a series of yags and their according slits.
    Automatically restore yags to OUT state and slits to initial position
    after running.    
    
    Paramaters
    ----------
    slit_set : [pcdsdevices.epics.slits.Slits,...]
        List of slits to be used for fiducialization process. yags and slits
        are paired elementwise and each pair is tested independantly. length
        of lists must match.
    
    yag_set : [pcdsdevices.epics.pim.PIM,...]
        List of yags to be used for fiducialization process. yags and slits are
        paired elementwise and each pair is tested independantly. length of
        lists must match.
    
    x_width : float, optional
        CHANGE SOON - this is the only one actually used 
    
    y_width : float, optional
        CHANGE SOON - passed down to ssf method but not used.
    
    samples : int, optional
        Number of shots to average over for measurments. 
    
    filters : dict, optional
        Filters to eliminate shots
    
    centroid : string, optional
        Field name of centroid measurement
        
    Returns
    -------
    [float,float,float...]
        This list of floats represents the field measured for each slit/yag
        pairing. The floats are in the same order as the slits and yags
        prsesented in the arguments. Length matches number of slit/yag pairs. 
    """

    if len(slit_set) != len(yag_set):
        raise Exception(
            "Number of slits, yags does not match. Cannot be paired"
        )
    
    results = []
    for slit, yag in zip(slit_set,yag_set):
        '''
        fiducial = yield from stage_wrapper(slit_scan_fiducialize,[slit,yag])(
            slit,
            yag,
            x_width,
            y_width,
            samples = samples,
            filters = filters,
            centroid = centroid, 
        )
        '''
        wrapped = stage_wrapper(
            partial(
                slit_scan_fiducialize,
                slit,
                yag,
                x_width,
                y_width,
                samples = samples,
                filters = filters,
                centroid = centroid,
            )(),
            [slit,yag]
        )
        fiducial = yield from wrapped
        results.append(fiducial)
    return results

