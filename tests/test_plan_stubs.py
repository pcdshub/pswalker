#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from queue import Queue
import functools
import logging

from bluesky.plans import run_wrapper

from pswalker.plan_stubs import (prep_img_motors, as_list, verify_all,
                                 match_condition, recover_threshold)
from pswalker.utils.exceptions import RecoverDone, RecoverFail
from .utils import plan_stash, SlowSoftPositioner, MotorSignal

logger = logging.getLogger(__name__)
tmo = 10


def test_prep_img_motors(RE, fake_yags):
    yags = fake_yags[0]
    for i in range(len(yags)):
        for prev_out in (True, False):
            for tail_in in (True, False):
                scan = prep_img_motors(i, yags, prev_out=prev_out,
                                       tail_in=tail_in)
                RE(scan)
                assert yags[i].blocking, "Desired yag not moved in"
                if prev_out and i > 0:
                    for j in range(i - 1):
                        assert not yags[j].blocking, "Yags before desired " + \
                                "yag not moved out with prev_out=True."
                if tail_in:
                    for j in range(i + 1, len(yags)):
                        assert yags[j].blocking, "Yags after desired yag " + \
                                "not moved in with tail_in=True."


def test_as_list():
    assert as_list(None) == []
    assert as_list(5) == [5]
    assert as_list([1, 2, 3]) == [1, 2, 3]
    assert as_list((1, 2, 3)) == [1, 2, 3]
    assert as_list("apples") == ["apples"]


verify_and_stash = functools.partial(plan_stash, verify_all)


def test_verify_all_answers(RE, fake_yags):
    yags, ans = fake_yags
    ok_queue = Queue()

    # Check that all correct returns True, near correct returns True, and
    # completely wrong returns False.
    RE(run_wrapper(verify_and_stash(ok_queue, yags, 'centroid_x', ans, 1)))
    RE(run_wrapper(verify_and_stash(ok_queue, yags, 'centroid_x',
                                    [a + 5 for a in ans], 6)))
    RE(run_wrapper(verify_and_stash(ok_queue, yags, 'centroid_x',
                                    [a + 5 for a in ans], 1)))
    assert ok_queue.get() is True, "Exactly correct rejected!"
    assert ok_queue.get() is True, "Within tolerance rejected!"
    assert ok_queue.get() is False, "Outside of tolerance accepted!"


def test_verify_all_readers(RE, fake_yags):
    yags, ans = fake_yags
    ok = False

    RE(run_wrapper(verify_all(yags[1:], 'centroid_x', ans, 5,
                              other_readers=yags[0],
                              other_fields='centroid_y')))
    for msg in RE.msg_hook.msgs:
        if msg.command == 'read' and yags[0] is msg.obj:
            ok = True
            break
    assert ok, ("We didn't find our extra reader in the collected messages")


def test_verify_all_array(RE, fake_yags):
    yags, ans = fake_yags
    ok_queue = Queue()

    # Last let's make sure we can get a list of bools that correspond correctly
    # to the yag that was wrong
    ans[0] = ans[0] + 25
    RE(run_wrapper(verify_and_stash(ok_queue, yags, 'centroid_x', ans, 5,
                                    summary=False)))
    ok_list = ok_queue.get()
    assert not ok_list[0], "Wrong element bool i=0"
    for i in range(1, len(ans)):
        assert ok_list[i], "Wrong element bool i={}".format(i)


@pytest.fixture(scope='function')
def mot_and_sig():
    mot = SlowSoftPositioner(n_steps=1000, delay=0.001, position=0,
                             name='test_mot', limits=(-100, 100))
    sig = MotorSignal(mot, name='test_sig')
    return mot, sig


@pytest.mark.timeout(tmo)
def test_match_condition_fixture(mot_and_sig):
    mot, sig = mot_and_sig
    mot.move(5)
    assert sig.value == 5
    mot.move(20, wait=False)
    mot.stop()
    assert mot.position < 20


@pytest.mark.timeout(tmo)
def test_match_condition_success(RE, mot_and_sig):
    logger.debug("test_match_condition_success")
    mot, sig = mot_and_sig
    RE(run_wrapper(match_condition(sig, lambda x: x > 10, mot, 20)))
    assert mot.position < 11
    # If the motor stopped shortly after 10, we matched the condition and
    # stopped


@pytest.mark.timeout(tmo)
def test_match_condition_fail(RE, mot_and_sig):
    logger.debug("test_match_condition_fail")
    mot, sig = mot_and_sig
    RE(run_wrapper(match_condition(sig, lambda x: x > 50, mot, 40)))
    assert mot.position == 40
    # If the motor did not stop and reached 40, we didn't erroneously match the
    # condition


@pytest.mark.timeout(tmo)
def test_match_condition_timeout(RE, mot_and_sig):
    logger.debug("test_match_condition_timeout")
    mot, sig = mot_and_sig
    RE(run_wrapper(match_condition(sig, lambda x: x > 9, mot, 5, timeout=0.3)))
    assert mot.position < 5
    # If the motor did not reach 5, we timed out


@pytest.mark.timeout(tmo)
def test_recover_threshold_success(RE, mot_and_sig):
    logger.debug("test_recover_threshold_success")
    mot, sig = mot_and_sig
    with pytest.raises(RecoverDone):
        RE(run_wrapper(recover_threshold(sig, 20, mot, +1)))
    assert mot.position < 21
    # If we stopped right after 20, we recovered


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
