#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import numpy as np
import pytest
from bluesky.plans import (open_run, close_run, create, read, save, mv,
                           checkpoint, run_wrapper)
from pswalker.skywalker import skywalker
from .utils import collector, MotorSignal

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("goal1", [0, 100])
@pytest.mark.parametrize("goal2", [0,-100])
@pytest.mark.parametrize("start1", [0., 150.0])
@pytest.mark.parametrize("start2", [0.,-150.0])
def test_skywalker(RE, slow_lcls_two_bounce_system,
                   start1, start2, goal1, goal2):
    logger.debug(("test_skywalker_main with, "
                  "goal1=%s, goal2=%s, start1=%s, start2=%s"),
                  goal1, goal2, start1, start2)
    s, m1, m2, y1, y2 = slow_lcls_two_bounce_system
    m1.set(start1)
    m2.set(start2)
    goal1 += y1.size[0]/2
    goal2 += y2.size[0]/2

    step = 100
    tmo = 5

    plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x', 'pitch',
                     [goal1, goal2], first_steps=step, tolerances=2,
                     averages=1, timeout=tmo, sim=True)

    RE(plan)
    y1.move_in()
    y2.move_in()
    assert np.isclose(y1.detector.centroid_x, 480 - goal1, atol=2)
    assert np.isclose(y2.detector.centroid_x, 480 - goal2, atol=2)
