#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import pytest
import numpy as np
from pswalker.skywalker import skywalker

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason='deprecated')
def test_skywalker(RE, slow_lcls_two_bounce_system):
    goal1 = 0
    goal2 = 0
    start1 = 0
    start2 = 0
    logger.debug(("test_skywalker_main with, "
                  "goal1=%s, goal2=%s, start1=%s, start2=%s"),
                 goal1, goal2, start1, start2)
    s, m1, m2, y1, y2 = slow_lcls_two_bounce_system
    m1.set(start1)
    m2.set(start2)
    goal1 += y1.size[0]/2
    goal2 += y2.size[0]/2

    step = 100
    tmo = 600

    plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x', 'pitch',
                     [goal1, goal2], first_steps=step, tolerances=2,
                     averages=50, timeout=tmo, sim=True)

    RE(plan)
    y1.move_in()
    y2.move_in()
    assert np.isclose(y1.detector.centroid_x, 480 - goal1, atol=2)
    assert np.isclose(y2.detector.centroid_x, 480 - goal2, atol=2)
