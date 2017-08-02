#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import threading
import uuid
import logging

from bluesky.plans import wait as plan_wait, abs_set, create, read, save
from bluesky.utils import FailedStatus

from .plans import measure_average
from .utils.argutils import as_list, field_prepend
from .utils.exceptions import BeamNotFoundError
from math import nan, isnan

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


def verify_all(detectors, target_fields, target_values, tolerances,
               other_readers=None, other_fields=None, average=1, delay=None,
               summary=True):
    """
    Plan to double-check the values on each of our imagers. Manipulates the
    yags, checks the values, and tells us which are ok.

    Parameters
    ----------
    detectors: list of Devices, or Device
        These are the imagers we're checking individually. They should have set
        methods that accept "IN" and "OUT" so we can manipulate their states as
        well as the Reader interface so we can get their values. These are
        assumed to block beam. This will accept a single Device instead of a
        list of there is only one.

    target_fields: list of str, or a str
        The field to verify for each detector, or a single field to use for
        every detector.

    target_values: list of numbers, or a number
        The value we're looking for at each detector, or a single value for
        every detector.

    tolerances: list of numbers, or a number
        The allowed delta from the target_value for each detector, or a single
        delta for every detector.

    other_readers: list of Devices or Device, optional
        Other readers to read and include in events while we're doing
        everything else.

    other_fields: list of str or str, optional
        The fields to read from our other_readers.

    average: int, optional
        Number of events to average over for the measurement

    delay: number, optional
        Time to wait between measurements during an average.

    summary: bool, optional
        If True, return a single boolean for the entire system. If False,
        return individual booleans for each detector.

    Returns
    -------
    ok: bool or list of bool
        If summary is True, we'll get a single boolean that is True if all of
        the detector readouts are verified and False otherwise. If summary is
        False, we'll get a list of booleans, one for each detector.
    """
    # Allow variable inputs
    detectors = as_list(detectors)
    num = len(detectors)
    target_fields = as_list(target_fields, length=num)
    target_values = as_list(target_values, length=num)
    tolerances = as_list(tolerances, length=num)
    other_readers = as_list(other_readers)
    other_fields = as_list(other_fields)

    # Build the ok list using our plans
    ok_list = []
    for i, (det, fld, val, tol) in enumerate(zip(detectors, target_fields,
                                                 target_values, tolerances)):
        ok = yield from prep_img_motors(i, detectors, timeout=15)
        if not ok:
            err = "Detector motion timed out!"
            logger.error(err)
            raise RuntimeError(err)
        avgs = yield from measure_average([det] + other_readers,
                                          num=average, delay=delay)
        #Check the tolerance of detector measurement
        ok_list.append(abs(avgs[field_prepend(fld,det)] - val) < tol)

    # Output for yield from
    output = all(ok_list)
    logger.debug("verify all complete for %s", detectors)
    if output:
        logger.debug("verify success")
    else:
        logger.debug("verify failed, bool is %s", ok_list)

    if summary:
        return output
    else:
        return ok_list


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
        logger.debug("condition FAIL in match_condition, mover=%s setpt=%s",
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
    yield from abs_set(slits,x=x_width,y = y_width)

    # read profile dimensions from image (width plugin pending)
    yag_measurements = yield from measure_average(
        [yag],
        num=samples
    )

    # extract measurements of interest from returned dict
    yag_measured_x_width = yag_measurements['xwidth']
    yag_measured_y_width = yag_measurements['ywidth']

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
    (float,float)
        (x,y) coordinates of centroid position in pixel space
    """
    #Set slits
    yield from abs_set(slits, wait=True,
                       xwidth = x_width,
                       ywidth = y_width)

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




