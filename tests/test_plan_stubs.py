#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import time
from queue import Queue

from ophyd import Signal
from ophyd.positioner import SoftPositioner
from bluesky import RunEngine
from bluesky.plans import run_wrapper

from pswalker.plan_stubs import (prep_img_motors, as_list, verify_all,
                                 match_condition, recover_threshold)
from pswalker.examples import YAG


def test_prep_img_motors(fake_path_two_bounce):
    path = fake_path_two_bounce
    yags = [d for d in path.devices if isinstance(d, YAG)]
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


def test_verify_all(fake_path_two_bounce):
    path = fake_path_two_bounce
    yags = [d for d in path.devices if isinstance(d, YAG)]
    RE = RunEngine({})
    ok_queue = Queue()

    def verify_and_stash(*args, **kwargs):
        ok = yield from run_wrapper(verify_all(*args, **kwargs))
        ok_queue.put(ok)

    # Pretend that the correct values are the current values
    ans = [y.read()['centroid_x']['value'] for y in yags]

    # Check that all correct returns True, near correct returns True, and
    # completely wrong returns False.
    RE(verify_and_stash(yags, 'centroid_x', ans, 1))
    RE(verify_and_stash(yags, 'centroid_x', [a + 5 for a in ans], 6))
    RE(verify_and_stash(yags, 'centroid_x', [a + 5 for a in ans], 1))
    assert ok_queue.get() is True, "Exactly correct rejected!"
    assert ok_queue.get() is True, "Within tolerance rejected!"
    assert ok_queue.get() is False, "Outside of tolerance accepted!"

    # Now let's check that other_readers are included
    ok = False
    for msg in verify_all(yags, 'centroid_x', ans, 5, other_readers="cow",
                          other_fields="milk"):
        if msg.command == "read" and msg.args[0] == "cow":
            ok = True
            break
    assert ok, "We didn't find our extra reader in the read messages..."

    # Last let's make sure we can get a list of bools that correspond correctly
    # to the yag that was wrong
    ans[0] = ans[0] + 25
    RE(verify_and_stash(yags, 'centroid_x', ans, 5, summary=False))
    ok_list = ok_queue.get()
    assert ok_list[0] is False, "Wrong element bool i=0"
    for i in range(1, len(ans)):
        assert ok_list[i] is True, "Wrong element bool i={}".format(i)


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

        for p in pos_list:
            if not self._stopped:
                time.sleep(self.delay)
                self._set_position(p)
        self._done_moving()

    def stop(self, *, success=False):
        self._stopped = True


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


match_condition = run_wrapper(match_condition)
recover_threashold = run_wrapper(recover_threshold)


def test_match_condition_fixture(mot_and_sig):
    mot, sig = mot_and_sig
    mot.move(5)
    assert sig.value == 5
    mot.move(20)
    mot.stop()
    assert mot.position < 20


def test_match_condition_success(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(match_condition(sig, lambda x: x > 10, mot, 20))
    assert mot.position < 11
    # If the motor stopped shortly after 10, we matched the condition and
    # stopped


def test_match_condition_fail(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(match_condition(sig, lambda x: x > 50, mot, 40))
    assert mot.position == 40
    # If the motor did not stop and reached 40, we didn't erroneously match the
    # condition


def test_match_condition_timeout(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(match_condition(sig, lambda x: x > 50, mot, 5, timeout=0.3))
    assert mot.position < 5
    # If the motor did not reach 5, we timed out


def test_recover_threshold_success(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(recover_threshold(sig, 20, mot, +1))
    assert mot.position < 21
    # If we stopped right after 20, we recovered


def test_recover_threshold_success_reverse(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(recover_threshold(sig, -1, mot, +1))
    assert mot.position > -2
    # If we stopped right after -1, we recovered


def test_recover_threshold_failure(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(recover_threshold(sig, 101, mot, +1))
    assert mot.position == -100
    # We got to the end of the negative direction, we failed


def test_recover_threshold_timeout_failure(mot_and_sig):
    mot, sig = mot_and_sig
    RE = RunEngine({})
    RE(recover_threshold(sig, 50, mot, +1, timeout=0.2))
    assert mot.position not in (50, 100, -100)
    # If we didn't reach the goal or either end, we timed out
