#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


def test_verify_all():
    verify_all
    pass  # idk yet


def test_match_condition():
    match_condition
    pass  # idk yet


def test_recover_threshold():
    recover_threshold
    pass  # idk yet
