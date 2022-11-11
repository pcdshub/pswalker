#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import threading
import time

import pytest
from bluesky.plan_stubs import checkpoint, create, mv, null, read, save, sleep
from bluesky.preprocessors import run_decorator
from bluesky.suspenders import SuspendFloor
from ophyd.signal import Signal

from ..suspenders import PvAlarmSuspend
from .utils import SlowSoftPositioner, collector

logger = logging.getLogger(__name__)


def test_pv_alarm_suspend_sanity():
    minor = PvAlarmSuspend("txt", "MINOR")  # NOQA
    major = PvAlarmSuspend("txt", "MAJOR")  # NOQA
    inval = PvAlarmSuspend("txt", "INVALID")  # NOQA
    with pytest.raises(TypeError):
        noalarm = PvAlarmSuspend("txt", "NO_ALARM")  # NOQA
    with pytest.raises(TypeError):
        adsfsdf = PvAlarmSuspend("txt", "adsfsdf")  # NOQA


# @pytest.mark.timeout(60)
@pytest.mark.skipif(True, reason="super long test")
def test_suspenders_stress(RE):
    """
    Run scan with tons of inconvenient suspenders
    """
    sig = Signal(name="dull signal")

    def pre_plan(*args, **kwargs):
        yield from null()
        logger.debug("starting suspender")

    def post_plan(*args, **kwargs):
        yield from null()
        logger.debug("releasing suspender")

    suspenders = [
        SuspendFloor(sig, i, sleep=10, pre_plan=pre_plan, post_plan=post_plan)
        for i in range(10)
    ]
    for s in suspenders:
        RE.install_suspender(s)
    mot = SlowSoftPositioner(n_steps=1000, delay=0.001, position=0, name="test_mot")

    def sig_sequence(sig):
        sig.put(15)
        time.sleep(1)
        sig.put(9)
        logger.debug("expect suspend soon")
        time.sleep(1)
        sig.put(8)
        logger.debug("expect second suspend layer")
        time.sleep(1)
        sig.put(14)
        logger.debug("expect resume after 1 second")
        time.sleep(2)
        sig.put(2)
        logger.debug("expect many layered suspend")
        time.sleep(1)
        sig.put(15)
        logger.debug("expect resume after 1 second")
        time.sleep(2)
        sig.put(-10)
        logger.debug("expect to confuse the scan now")
        sig.put(10)
        sig.put(3)
        sig.put(5)
        sig.put(456)
        sig.put(0)
        sig.put(23)
        sig.put(0)
        sig.put(15)
        logger.debug("hopefully it suspended and is now waiting to resume")
        # 3 suspends and 3 resumes should add 6s to the scan

    @run_decorator()
    def dull_scan(mot, count, sig=None, sleep_time=0):
        if sig:
            thread = threading.Thread(target=sig_sequence, args=(sig,))
            thread.start()
        for i in range(count):
            yield from checkpoint()
            try:
                yield from mv(mot, i)
            except Exception:
                pass
            # make every step take 1s extra
            yield from sleep(sleep_time)
            yield from checkpoint()
            yield from create()
            yield from read(mot)
            yield from save()
            yield from checkpoint()

    out = []
    coll = collector("test_mot", out)
    RE.subscribe("event", coll)

    base_start = time.time()
    RE(dull_scan(mot, 10, sleep_time=1))
    base_elapsed = time.time() - base_start

    susp_start = time.time()
    RE(dull_scan(mot, 10, sig=sig, sleep_time=1))
    susp_elapsed = time.time() - susp_start

    assert susp_elapsed - base_elapsed > 6
