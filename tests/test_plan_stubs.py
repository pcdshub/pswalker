#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import time
from queue import Queue
import threading
import logging

from ophyd import Signal
from ophyd.positioner import SoftPositioner
from bluesky import RunEngine
from bluesky.plans import run_wrapper

from pswalker.plan_stubs import (prep_img_motors, as_list, verify_all,
                                 match_condition, recover_threshold)
from pswalker.examples import YAG

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_yags(fake_path_two_bounce):
    path = fake_path_two_bounce
    yags = [d for d in path.devices if isinstance(d, YAG)]

    # Pretend that the correct values are the current values
    ans = [y.read()['centroid_x']['value'] for y in yags]

    return yags, ans


def test_prep_img_motors(fake_yags):
    yags = fake_yags[0]
    RE = RunEngine({})
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


def verify_and_stash(ok_queue, *args, **kwargs):
    ok = yield from verify_all(*args, **kwargs)
    ok_queue.put(ok)


def test_verify_all_answers(fake_yags):
    yags, ans = fake_yags
    RE = RunEngine({})
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


def make_store_doc(dest, filter_doc_type='all'):
    def store_doc(doc_type, doc):
        if filter_doc_type == 'all' or doc_type == filter_doc_type:
            dest.append(doc)
    return store_doc


def test_verify_all_readers(fake_yags):
    yags, ans = fake_yags
    ok = False
    RE = RunEngine({})

    descr = []
    store_doc = make_store_doc(descr, 'descriptor')

    RE(run_wrapper(verify_all(yags[1:], 'centroid_x', ans, 5,
                              other_readers=yags[0],
                              other_fields='centroid_y')), store_doc)
    for desc in descr:
        if yags[0].name in desc['object_keys'].keys():
            ok = True
            break
    assert ok, ("We didn't find our extra reader in the descriptor docs")


def test_verify_all_array(fake_yags):
    yags, ans = fake_yags
    RE = RunEngine({})
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


class SlowSoftPositioner(SoftPositioner):
    """
    Soft positioner that moves to the destination slowly, like a real motor
    """
    def __init__(self, *, n_steps, delay, position, **kwargs):
        super().__init__(**kwargs)
        self.n_steps = n_steps
        self.delay = delay
        self._position = position
        self._stopped = False

    def _setup_move(self, position, status):
        self._run_subs(sub_type=self.SUB_START, timestamp=time.time())

        self._started_moving = True
        self._moving = True
        self._stopped = False

        delta = (position - self.position)/self.n_steps
        pos_list = [self.position + n * delta for n in range(1, self.n_steps)]
        pos_list.append(position)

        thread = threading.Thread(target=self._move_thread,
                                  args=(pos_list, status))
        logger.debug("test motor start moving")
        thread.start()

    def stop(self, *, success=False):
        self._stopped = True
        logger.debug("stop test motor")

    def _move_thread(self, pos_list, status):
        ok = True
        for p in pos_list:
            if self._stopped:
                ok = False
                break
            if not self._stopped:
                time.sleep(self.delay)
                self._set_position(p)
        self._done_moving(success=ok)
        logger.debug("test motor done moving")


class MotorSignal(Signal):
    """
    Signal that reports its value to be that of a given positioner object
    """
    def __init__(self, motor, name=None, parent=None):
        super().__init__(name=name, parent=parent)
        motor.subscribe(self.put_cb)

    def put_cb(self, *args, value, **kwargs):
        self.put(value)


@pytest.fixture(scope='function')
def mot_and_sig():
    mot = SlowSoftPositioner(n_steps=1000, delay=0.001, position=0,
                             name='test_mot', limits=(-100, 100))
    sig = MotorSignal(mot, name='test_sig')
    return mot, sig


@pytest.mark.timeout(5)
def test_match_condition_fixture(mot_and_sig):
    mot, sig = mot_and_sig
    mot.move(5)
    assert sig.value == 5
    mot.move(20, wait=False)
    mot.stop()
    assert mot.position < 20


@pytest.mark.timeout(5)
def test_match_condition_success(mot_and_sig):
    logger.debug("test_match_condition_success")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(match_condition(sig, lambda x: x > 10, mot, 20)))
    assert mot.position < 11
    # If the motor stopped shortly after 10, we matched the condition and
    # stopped


@pytest.mark.timeout(5)
def test_match_condition_fail(mot_and_sig):
    logger.debug("test_match_condition_fail")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(match_condition(sig, lambda x: x > 50, mot, 40)))
    assert mot.position == 40
    # If the motor did not stop and reached 40, we didn't erroneously match the
    # condition


@pytest.mark.timeout(5)
def test_match_condition_timeout(mot_and_sig):
    logger.debug("test_match_condition_timeout")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(match_condition(sig, lambda x: x > 9, mot, 5, timeout=0.3)))
    assert mot.position < 5
    # If the motor did not reach 5, we timed out


@pytest.mark.timeout(5)
def test_recover_threshold_success(mot_and_sig):
    logger.debug("test_recover_threshold_success")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(recover_threshold(sig, 20, mot, +1)))
    assert mot.position < 21
    # If we stopped right after 20, we recovered


@pytest.mark.timeout(5)
def test_recover_threshold_success_reverse(mot_and_sig):
    logger.debug("test_recover_threshold_success_reverse")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(recover_threshold(sig, -1, mot, +1)))
    assert mot.position > -2
    # If we stopped right after -1, we recovered


@pytest.mark.timeout(5)
def test_recover_threshold_failure(mot_and_sig):
    logger.debug("test_recover_threshold_failure")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(recover_threshold(sig, 101, mot, +1)))
    assert mot.position == -99.999
    # We got to the end of the negative direction, we failed


@pytest.mark.timeout(5)
def test_recover_threshold_timeout_failure(mot_and_sig):
    logger.debug("test_recover_threshold_timeout_failure")
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(run_wrapper(recover_threshold(sig, 50, mot, +1, timeout=0.2)))
    assert mot.position not in (50, 99.999, -99.999)
    # If we didn't reach the goal or either end, we timed out
