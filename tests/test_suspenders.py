#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import random

import pytest
from bluesky import RunEngine
from bluesky.plans import sleep, checkpoint

from pswalker.examples import YAG
from pswalker.suspenders import (LightpathSuspender, BeamEnergySuspendFloor,
                                 BeamRateSuspendFloor)


def ruin_my_path(path):
    choices = [d for d in path.devices if isinstance(d, YAG)]
    device = random.choice(choices)
    device.set("IN")


def sleepy_scan():
    yield from checkpoint()
    yield from sleep(0.2)


@pytest.mark.timeout(5)
def test_lightpath_suspender(fake_path_two_bounce):
    path = fake_path_two_bounce
    path.clear(wait=True)
    suspender = LightpathSuspender(None, path=path)
    RE = RunEngine()
    RE.install_suspender(suspender)
    loop = RE._loop

    # Run once to make sure the test scan isn't bad
    RE(sleepy_scan())
    assert RE.state == "idle"

    start = time.time()
    # Queue up fail/resume conditions
    loop.call_later(0.1, ruin_my_path, path)
    loop.call_later(0.5, path.clear)

    # Run again
    RE(sleepy_scan())
    stop = time.time()

    delta = stop - start
    assert delta > 0.3, "Suspender did not suspend"
    assert delta > 0.7, "Suspender resumed early"
    assert delta < 1.5, "Suspender resumed suspiciously late"


def test_beam_suspenders_sanity():
    """
    Just instantiate them to check for silly errors. It should work.
    """
    energy = BeamEnergySuspendFloor(0.3) # NOQA
    rate = BeamRateSuspendFloor(0) # NOQA
