#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import logging
from queue import Queue

from bluesky.plans import run_wrapper, run_decorator, null
from ophyd.device import Staged

from pswalker.recovery import recover_threshold, needs_recovery
from pswalker.utils.exceptions import RecoverDone, RecoverFail

logger = logging.getLogger(__name__)
tmo = 10


@pytest.mark.timeout(tmo)
def test_recover_threshold_success(RE, mot_and_sig):
    logger.debug("test_recover_threshold_success")
    mot, sig = mot_and_sig
    with pytest.raises(RecoverDone):
        RE(run_wrapper(recover_threshold(sig, 20, mot, +1)))
    assert mot.position < 21
    # If we stopped right after 20, we recovered


@pytest.mark.timeout(tmo)
def test_recover_threshold_success_no_stop(RE, mot_and_sig):
    logger.debug("test_recover_threshold_success_no_stop")
    mot, sig = mot_and_sig
    mot.delay = 0
    with pytest.raises(RecoverDone):
        RE(run_wrapper(recover_threshold(sig, 20, mot, +1, has_stop=False)))
    assert 59 < mot.position < 61
    # If we went halfway between 20 and 100, it worked


@pytest.mark.timeout(tmo)
def test_recover_threshold_success_reverse(RE, mot_and_sig):
    logger.debug("test_recover_threshold_success_reverse")
    mot, sig = mot_and_sig
    with pytest.raises(RecoverDone):
        RE(run_wrapper(recover_threshold(sig, -1, mot, +1)))
    assert mot.position > -2
    # If we stopped right after -1, we recovered


@pytest.mark.timeout(tmo)
def test_recover_threshold_failure(RE, mot_and_sig):
    logger.debug("test_recover_threshold_failure")
    mot, sig = mot_and_sig
    with pytest.raises(RecoverFail):
        RE(run_wrapper(recover_threshold(sig, 101, mot, +1)))
    assert mot.position == -100
    # We got to the end of the negative direction, we failed


@pytest.mark.timeout(tmo)
def test_recover_threshold_failure_no_stop(RE, mot_and_sig):
    logger.debug("test_recover_threshold_failure_no_stop")
    mot, sig = mot_and_sig
    mot.delay = 0
    with pytest.raises(RecoverFail):
        RE(run_wrapper(recover_threshold(sig, 101, mot, +1, has_stop=False)))
    assert mot.position == -100
    # We got to the end of the negative direction, we failed


@pytest.mark.timeout(tmo)
def test_recover_threshold_timeout_failure(RE, mot_and_sig):
    logger.debug("test_recover_threshold_timeout_failure")
    mot, sig = mot_and_sig
    # Make the motor slower to guarantee a timeout
    mot.n_steps = 5000
    with pytest.raises(RecoverFail):
        RE(run_wrapper(recover_threshold(sig, 50, mot, +1, timeout=0.1)))
    pos = mot.position
    assert not 49 < pos < 51
    assert mot.position not in (100, -100)
    # If we didn't reach the goal or either end, we timed out


def test_needs_recovery(RE):
    logger.debug("test_needs_recovery")
    # Need to make sure the RE runs the plan and that internally it returns the
    # detectors that need recovering.

    class Det:
        def __init__(self, value, staged):
            self.value = value
            self._staged = staged
    return_values = Queue()

    def is_ok_det(det):
        yield from null()
        return det.value > 2

    @run_decorator()
    def call_and_stash(plan, plan_args, stash):
        val = yield from plan(*plan_args)
        stash.put(val)

    dets = Det(4, Staged.yes)
    RE(call_and_stash(needs_recovery, [dets, is_ok_det], return_values))
    assert return_values.get() == []

    dets = Det(0, Staged.yes)
    RE(call_and_stash(needs_recovery, [dets, is_ok_det], return_values))
    assert return_values.get() == [dets]

    dets = Det(0, Staged.no)
    RE(call_and_stash(needs_recovery, [dets, is_ok_det], return_values))
    assert return_values.get() == []

    dets = [Det(0, Staged.yes), Det(0, Staged.yes)]
    RE(call_and_stash(needs_recovery, [dets, is_ok_det], return_values))
    assert return_values.get() == [dets[0]]

    dets = [Det(0, Staged.yes), Det(0, Staged.yes)]
    RE(call_and_stash(needs_recovery, [dets, is_ok_det, False], return_values))
    assert return_values.get() == dets
