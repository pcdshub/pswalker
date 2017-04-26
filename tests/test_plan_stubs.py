#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue

from bluesky import RunEngine

from pswalker.plan_stubs import (prep_img_motors, ensure_list, verify_all,
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


def test_ensure_list():
    assert ensure_list(None) == []
    assert ensure_list(5) == [5]
    assert ensure_list([1, 2, 3]) == [1, 2, 3]
    assert ensure_list((1, 2, 3)) == [1, 2, 3]


def test_verify_all(fake_path_two_bounce):
    path = fake_path_two_bounce
    yags = [d for d in path.devices if isinstance(d, YAG)]
    RE = RunEngine()
    ok_queue = Queue()

    def verify_and_stash(*args, **kwargs):
        ok = yield from verify_all(*args, **kwargs)
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


def test_match_condition():
    match_condition
    pass  # idk yet


def test_recover_threshold():
    recover_threshold
    pass  # idk yet
