#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import threading
import uuid
import logging

from bluesky.plans import (wait as plan_wait, abs_set, stop, create, read,
                           save)

from .plans import measure_average
from .utils.argutils import as_list

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

    ok = time.time() - start_time < timeout
    if ok:
        logger.debug("prep_img_motors completed successfully")
    else:
        logger.debug("prep_img_motors exitted with timeout")
    return ok


def verify_all(detectors, target_fields, target_values, tolerances,
               other_readers=None, other_fields=None, average=None, delay=None,
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
    target_fields = as_list(target_fields)
    target_values = as_list(target_values)
    tolerances = as_list(tolerances)
    other_readers = as_list(other_readers)
    other_fields = as_list(other_fields)

    # Build the ok list using our plans
    ok = []
    for i, (det, fld, val, tol) in enumerate(zip(detectors, target_fields,
                                                 target_values, tolerances)):
        ok = yield from prep_img_motors(i, detectors, timeout=15)
        if not ok:
            err = "Detector motion timed out!"
            logger.error(err)
            raise RuntimeError(err)
        avgs = yield from measure_average([det] + other_readers,
                                          [fld] + other_fields,
                                          num=average, delay=delay)
        try:
            avg = avgs[0]
        except:
            avg = avgs
        ok.append(abs(avg - val) < tol)

    # Output for yield from
    output = all(ok)
    if output:
        logger.debug("verify complete, all ok")
    else:
        logger.debug("verify failed! bool is %s", ok)

    if summary:
        return output
    else:
        return ok


def match_condition(signal, condition, mover, setpoint, timeout=None,
                    sub_type=None):
    """
    Plan to adjust mover until condition() returns True. Read and save both the
    signal and the mover after the move.

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

    Returns
    -------
    ok: bool
        True if we reached the condition, False if we timed out or reached the
        setpoint before satisfying the condition.
    """
    done = threading.Event()
    success = threading.Event()

    def condition_cb(*args, value, **kwargs):
        if condition(value):
            success.set()
            done.set()

    def dmov_cb(*args, **kwargs):
        logger.debug("motor stopped moving in match_condition")
        done.set()

    if sub_type is not None:
        signal.subscribe(condition_cb, sub_type=sub_type)
    else:
        signal.subscribe(condition_cb)

    yield from abs_set(mover, setpoint, moved_cb=dmov_cb)
    done.wait(float(timeout))
    yield from stop(mover)
    yield from create()
    yield from read(mover)
    yield from read(signal)
    yield from save()
    signal.unsubscribe(condition_cb)

    ok = success.is_set()
    if ok:
        logger.debug("condition met in match_condition, mover=%s setpt=%s",
                     mover.name, setpoint)
    else:
        logger.debug("condition FAIL in match_condition, mover=%s setpt=%s",
                     mover.name, setpoint)
    return ok


def recover_threshold(signal, threshold, motor, dir_initial, dir_timeout=None,
                      try_reverse=True, ceil=True):
    """
    Plan to move motor towards each limit switch until the signal is above a
    threshold value.

    Parameters
    ----------
    signal: Signal
        Object that implements the Bluesky "readable" interface, including the
        optional subscribe function, sending at least the keyword "value" as in
        ophyd.Signal.

    threshold: number
        When signal is equal to or greater than this value, we've recovered.

    motor: Motor
        Object that implements the "readable" and "movable" interfaces, accepts
        "moved_cb" as a keyword argument, and has signals at attributes
        high_limit_switch and low_limit_switch

    dir_initial: int
        1 if we're going to the positive limit switch, -1 otherwise.

    dir_timeout: float, optional
        If we don't reach the threshold in this many seconds, try the other
        direction.

    try_reverse: bool, optional
        If True, switch and try the other limit switch if the first direction
        fails.

    ceil: bool, optional
        If True, we're look for signal >= threshold (default).
        If False, look for signal <= threshold instead.
    """
    if dir_initial > 0:
        logger.debug("Recovering towards the high limit switch")
        setpoint = motor.high_limit_switch.get() - 0.001
    else:
        logger.debug("Recovering towards the low limit switch")
        setpoint = motor.low_limit_switch.get() + 0.001

    def condition(x):
        if ceil:
            return x >= threshold
        else:
            return x <= threshold
    ok = yield from match_condition(signal, condition, motor, setpoint,
                                    timeout=dir_timeout)
    if ok:
        logger.debug("Recovery was successful")
        return True
    else:
        if try_reverse:
            logger.debug("First direction failed, trying reverse...")
            return (yield from recover_threshold(signal, threshold, motor,
                                                 -dir_initial,
                                                 dir_timeout=2*dir_timeout,
                                                 try_reverse=False))
        else:
            logger.debug("Recovery failed")
            return False
