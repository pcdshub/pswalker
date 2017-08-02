#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from .plan_stubs import match_condition

logger = logging.getLogger(__name__)


def recover_threshold(signal, threshold, motor, dir_initial, timeout=None,
                      try_reverse=True, ceil=True, off_limit=0, has_stop=True):
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

    timeout: float, optional
        If we don't reach the threshold in this many seconds, try the other
        direction.

    try_reverse: bool, optional
        If True, switch and try the other limit switch if the first direction
        fails.

    ceil: bool, optional
        If True, we're look for signal >= threshold (default).
        If False, look for signal <= threshold instead.

    off_limit: float, optional
        The distance from the limit to aim for. This is included because some
        motor implementations do not allow us to move exactly to the limit. If
        this is the case, set it to some small value compared to your move
        sizes.

    has_stop: bool, optional
        Boolean to indicate whether or not we can stop the motor. We usually
        use the motor's stop command to stop when recovered. If this is set to
        False (e.g. we can't stop it), go back to center of the largest range
        with the signal above the threshold.

    Returns
    -------
    success: bool
        True if we had a successful recovery, False otherwise.
    """
    logger.debug(("Recover threshold with signal=%s, threshold=%s, motor=%s, "
                  "dir_initial=%s, timeout=%s"), signal, threshold, motor,
                 dir_initial, timeout)
    if dir_initial > 0:
        logger.debug("Recovering towards the high limit switch")
        setpoint = motor.high_limit - off_limit
    else:
        logger.debug("Recovering towards the low limit switch")
        setpoint = motor.low_limit + off_limit

    def condition(x):
        if ceil:
            return x >= threshold
        else:
            return x <= threshold
    ok = yield from match_condition(signal, condition, motor, setpoint,
                                    timeout=timeout, has_stop=has_stop)
    if ok:
        logger.debug("Recovery was successful")
        return True
    else:
        if try_reverse:
            logger.debug("First direction failed, trying reverse...")
            if timeout is not None:
                timeout *= 2
            return (yield from recover_threshold(signal, threshold, motor,
                                                 -dir_initial,
                                                 timeout=timeout,
                                                 try_reverse=False,
                                                 ceil=ceil,
                                                 off_limit=off_limit))
        else:
            logger.debug("Recovery failed")
            return False


def homs_recovery(*, detectors, motors, goals, detector_fields, index,
                  sim=False):
    """
    Plan to recover the homs system should something go wrong. Is passed
    arguments as defined in iterwalk.
    """
    # Interpret args as homs mirrors and areadetector pims
    # Take the active mirror/pim pair
    yag = detectors[index]
    if sim:
        sig = yag.detector.stats2.centroid.x
    else:
        sig = yag.detector.stats2.centroid.y
    mirror = motors[index]
    try:
        # Try recover_threshold toward nominal position
        center = mirror.nominal_position
        if mirror.position < center:
            dir_initial = 1
        else:
            dir_initial = -1
    except AttributeError:
        # If no nominal position, do the shorter move first
        dist_to_high = abs(mirror.position - mirror.high_limit)
        dist_to_low = abs(mirror.position - mirror.low_limit)
        if dist_to_high < dist_to_low:
            dir_initial = 1
        else:
            dir_initial = -1
    # Call the threshold recovery
    ok = yield from recover_threshold(sig, 0.1, mirror, dir_initial,
                                      timeout=60, try_reverse=True,
                                      off_limit=0.001, has_stop=False)
    # Pass the return value back out
    return ok


def sim_recovery(*, detectors, motors, goals, detector_fields, index):
    return (yield from homs_recovery(detectors=detectors, motors=motors,
                                     goals=goals,
                                     detector_fields=detector_fields,
                                     index=index, sim=True))
