#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import threading
import uuid

from bluesky.plans import (wait as plan_wait, abs_set, rel_set, create, read,
                           save, checkpoint)

from .plans import measure_average


def prep_img_motors(n_mot, img_motors, prev_out=True, tail_in=True):
    """
    Plan to prepare image motors for taking data. Moves the correct imagers in
    and waits for them to be ready.

    Parameters
    ----------
    n_mot: int
        Index of the motor in img_motors that we need to take data with.
    img_motors: list of OphydObject
        OphydObjects to move in or out. These objects need to have .set methods
        that accept the strings "IN" and "OUT", reacting appropriately. These
        should be ordered by increasing distance to the source.
    prev_out: bool, optional
        If True, pull out imagers closer to the source than the one we need to
        use. Default True. (True if imager blocks beam)
    tail_in: bool, optional
        If True, put in imagers after this one, to be ready for later. If
        False, don't touch them. We won't wait for the tail motors to move in.
    """
    prev_img_mot = str(uuid.uuid4())
    for i, mot in enumerate(img_motors):
        if i < n_mot and prev_out:
            yield from abs_set(mot, "OUT", group=prev_img_mot)
        elif i == n_mot:
            yield from abs_set(mot, "IN", group=prev_img_mot)
        elif tail_in:
            yield from abs_set(mot, "IN")

    yield from plan_wait(group=prev_img_mot)


def ensure_list(obj):
    if obj is None:
        return []
    try:
        return list(obj)
    except:
        return [obj]


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
    detectors = ensure_list(detectors)
    target_fields = ensure_list(target_fields)
    target_values = ensure_list(target_values)
    tolerances = ensure_list(tolerances)
    other_readers = ensure_list(other_readers)
    other_fields = ensure_list(other_fields)

    # Build the ok list using our plans
    ok = []
    for i, (det, fld, val, tol) in enumerate(zip(detectors, target_fields,
                                                 target_values, tolerances)):
        yield from prep_img_motors(i, detectors)
        avgs = yield from measure_average([det] + other_readers,
                                          [fld] + other_fields,
                                          num=average, delay=delay)
        try:
            avg = avgs[0]
        except:
            avg = avgs
        ok.append(abs(avg - val) < tol)

    # Output for yield from
    if summary:
        return all(ok)
    else:
        return ok


def step_recover(detector, detector_field, threshold, mover,
                 step_size, change_direction=None, timeout=300):
    """
    Plan to be run when we have no signal on our detector because our mover is
    in a bad state. Step n times in one direction, then do the same in the
    other direction, then try the first direction again, etc.

    Parameters
    ----------
    detector: Device
        Something that we can read

    detector_field: str
        The field to use from our detector

    threshold: number
        We consider ourselves recovered if our reading is above the threshold.

    mover: Device
        Something we can set and read. Should have a position property.

    step_size: number
        The size and direction of our steps.

    change_direction: int, optional
        How many steps to take before changing directions.

    timeout: number, optional
        Abort the recovery after this amount of time.
    """
    def next_step():
        direction = 1
        i = 0
        n_swap = 0
        yield step_size
        while True:
            i += 1
            if change_direction and not i % change_direction:
                direction *= -1
                n_swap += 1
                yield step_size * direction * (change_direction * n_swap + 1)
            else:
                yield step_size * direction

    ok = False
    step_gen = next_step()
    start_time = time.time()
    while time.time() - start_time < timeout:
        yield from checkpoint()
        step = next(step_gen)
        yield from rel_set(mover, step, wait=True)
        yield from create()
        yield from read(mover)
        reading = yield from read(detector)
        yield from save()
        if reading >= threshold:
            ok = True
            break
    return ok


def match_condition(signal, condition, mover, setpoint, timeout=None,
                    sub_type=None):
    """
    Adjust mover until condition() returns True.

    Parameters
    ----------
    signal: Signal
        Object that has a subscribe() method that lets us set callbacks to run
        when a value changes, passing keyword "value" to the callback function.

        Signals that subclass ophyd.Signal should have these properties.

    condition: function
        Function that accepts a single argument, "value", and returns
        True or False.

    mover: Device
        Object that can be moved by calling set(position, moved_cb=cb) where
        set doesn't block and kwarg moved_cb causes cb(*args, **kwargs) to be
        called after motion and stopped by calling stop().

        Devices that subclass ophyd.positioner.PositionerBase should have these
        properties.

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
            mover.stop()
            done.set()

    def dmov_cb(*args, **kwargs):
        done.set()

    if sub_type is not None:
        signal.subscribe(condition_cb, sub_type=sub_type)
    else:
        signal.subscribe(condition_cb)

    mover.set(setpoint, moved_cb=dmov_cb)
    done.wait(float(timeout))

    return success.is_set()
