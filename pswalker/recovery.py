#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from threading import Lock

from bluesky.plans import checkpoint, plan_mutator, null
from ophyd.device import Staged

from .plan_stubs import match_condition, prep_img_motors
from .utils.argutils import as_list
from .utils.exceptions import RecoverDone, RecoverFail

logger = logging.getLogger(__name__)


def recover_threshold(signal, threshold, motor, dir_initial, timeout=None,
                      try_reverse=True, ceil=True, off_limit=0, has_stop=True):
    """
    Plan to move motor towards each limit switch until the signal is above a
    threshold value.

    Raises RecoverDone upon completion.

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
        raise RecoverDone
    else:
        if try_reverse:
            logger.debug("First direction failed, trying reverse...")
            if timeout is not None:
                timeout *= 2
            return (yield from recover_threshold(signal, threshold, motor,
                                                 -dir_initial,
                                                 timeout=timeout,
                                                 try_reverse=False,
                                                 ceil=ceil))
        else:
            logger.debug("Recovery failed")
            raise RecoverFail


def branching_plan(plan, branches, branch_choice, branch_msg='checkpoint'):
    """
    Plan that allows deviations from the original plan at checkpoints.

    Parameters
    ----------
    plan: iterable
        Iterable that returns Msg objects as in a Bluesky plan

    branches: list of functions
        Functions that return valid plans. These are the deviations we may take
        when plan yields a checkpoint.

    branch_choice: function
        Function that tells us which branch to take. This must return None when
        we want to continue to normal plan and an integer that matches an index
        in branches when we want to deviate.

    branch_msg: str, optional
        Which message to branch on. By default, this is checkpoint.
    """
    def do_branch():
        choice = branch_choice()
        if choice is None:
            yield null()
        else:
            branch = branches[choice]
            logger.debug("Switching to branch %s", choice)
            yield from branch()

    # No nested branches
    branch_lock = Lock()

    def branch_handler(msg):
        if msg.command == branch_msg:
            nonlocal branch_lock
            has_lock = branch_lock.acquire(blocking=False)
            if has_lock:
                try:
                    def new_gen():
                        nonlocal branch_lock
                        with branch_lock:
                            if branch_choice() is not None:
                                yield from checkpoint()
                                yield from do_branch()
                                logger.debug("Resuming plan after branch")
                            yield msg
                finally:
                    branch_lock.release()
                    return new_gen(), None
        return None, None

    brancher = plan_mutator(plan, branch_handler)
    return (yield from brancher)


def get_thresh_signal(yag):
    """
    Given a yag object, return the signal we'll be using to determine if the
    yag has beam on it.
    """
    return yag.detector.stats2.centroid.y


def make_homs_recover(yags, yag_index, motor, threshold, center=0,
                      get_signal=get_thresh_signal):
    """
    Make a recovery plan for a particular yag/motor combination in the homs
    system.
    """
    def homs_recover():
        sig = get_signal(yags[yag_index])
        if motor.position < center:
            dir_init = 1
        else:
            dir_init = -1

        def plan():
            yield from prep_img_motors(yag_index, yags, timeout=10)
            yield from recover_threshold(sig, threshold, motor, dir_init,
                                         timeout=120, has_stop=False)
        return (yield from plan())

    return homs_recover


def make_pick_recover(yag1, yag2, threshold):
    """
    Make a function of zero arguments that will determine if a recovery plan
    needs to be run, and if so, which plan to use.
    """
    def pick_recover():
        return None
        num = 25
        sigs = []
        if yag1.position == "IN":
            for i in range(num):
                sig = get_thresh_signal(yag1)
                sigs.append(sig)
            if max(sigs) < threshold[0]:
                return 0
            else:
                return None
        elif yag2.position == "IN":
            for i in range(num):
                sig = get_thresh_signal(yag2)
                sigs.append(sig)
            if max(sigs) < threshold[1]:
                return 1
            else:
                return None

    return pick_recover


def needs_recovery(dets, is_ok_plans, blocking=True):
    """
    Plan to determine if a recovery plan needs to be run, and if so, which
    detectors indicate a problem.

    Parameters
    ----------
    dets: Device or list of Devices
        If a list, these should be in the physical order along the beam line,
        upstream to downstream. These must implement the stage method and have
        the _staged enum so we can check if they are active or not.

    is_ok_plans: function or list of functions
        Function of one argument, taking in a detector and returning a plan
        that determines if the readback on the corresponding det object needs
        a recovery. This should use messages like "read", etc. to collect data
        in the bluesky framework rather than relying on direct function calls
        (though direct function calls will still work, at the expense of losing
        the niceness of the RunEngine). Remember that checkpoints are rewind
        points for suspenders and other interruptions.

    blocking: bool or list of bool
        If True, the upstream detectors block the downstream detectors, so we
        will stop after finding the first active detector.

    Returns
    -------
    dets_to_recover: list of objects
        All objects that indicate a recovery. An empty list means that no
        recovery is needed. If blocking is True, we expect length <= 1 because
        we'd stop checking after the first active det.
    """
    logger.debug("call needs_recovery(dets=%s, is_ok_plans=%s, blocking=%s)",
                 dets, is_ok_plans, blocking)
    dets = as_list(dets)
    num = len(dets)
    is_ok_plans = as_list(is_ok_plans, length=num)
    blocking = as_list(blocking, length=num)

    dets_to_recover = []
    for det, is_ok, block in zip(dets, is_ok_plans, blocking):
        yield from checkpoint()
        if det._staged == Staged.yes:
            ok = yield from is_ok(det)
            if not ok:
                dets_to_recover.append(det)
            if block:
                break

    return dets_to_recover
