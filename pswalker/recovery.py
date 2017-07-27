#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from threading import Lock

from bluesky.plans import checkpoint, plan_mutator, null

from .plan_stubs import match_condition
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
