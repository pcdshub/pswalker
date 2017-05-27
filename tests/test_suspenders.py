#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

import pytest

from pswalker.suspenders import (LightpathSuspender, BeamEnergySuspendFloor,
                                 BeamRateSuspendFloor, PvAlarmSuspend)
from .utils import ruin_my_path, sleepy_scan


@pytest.mark.timeout(5)
def test_lightpath_suspender(RE, fake_path_two_bounce):
    path = fake_path_two_bounce
    path.clear(wait=True)
    suspender = LightpathSuspender(None, path=path)
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


def test_pv_alarm_suspend_sanity():
    minor = PvAlarmSuspend("txt", "MINOR") # NOQA
    major = PvAlarmSuspend("txt", "MAJOR") # NOQA
    inval = PvAlarmSuspend("txt", "INVALID") # NOQA
    with pytest.raises(TypeError):
        noalarm = PvAlarmSuspend("txt", "NO_ALARM") # NOQA
    with pytest.raises(TypeError):
        adsfsdf = PvAlarmSuspend("txt", "adsfsdf") # NOQA
