#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import numpy as np
import pytest
from bluesky.plans import (open_run, close_run, create, read, save, mv,
                           checkpoint, run_wrapper)
from pswalker.skywalker import skywalker
from pswalker.utils.exceptions import RecoverDone
from .utils import collector, MotorSignal

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("use_recover", [False])
@pytest.mark.parametrize("goal1", [0, 100])
@pytest.mark.parametrize("goal2", [0,-100])
@pytest.mark.parametrize("start1", [0., 150.0])
@pytest.mark.parametrize("start2", [0.,-150.0])
def test_skywalker(RE, lcls_two_bounce_system,
                   start1, start2, goal1, goal2, use_recover):
    logger.debug(("test_skywalker_main with use_recover=%s, "
                  "goal1=%s, goal2=%s, start1=%s, start2=%s"),
                 use_recover, goal1, goal2, start1, start2)
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    m1.set(start1)
    m2.set(start2)
    goal1 += y1.size[0]/2
    goal2 += y2.size[0]/2
    range1 = [y1.size[0]/2 + x for x in [-500, 500]]
    range2 = [y2.size[0]/2 + x for x in [-500, 500]]

    step = 100
    def recover(motor, imager, imager_range):
        def recover_plan():
            logger.debug('run recovery plan')
            goal = np.mean(imager_range)
            pos1 = [motor.position, imager.detector.centroid_x]
            yield from mv(motor, motor.position + step)
            pos2 = [motor.position, imager.detector.centroid_x]
            slope = (pos2[0] - pos1[0]) / (pos2[1] - pos1[1])
            mot_target = slope*(goal-pos1[1]) + pos1[0]
            logger.debug('move %s from %s to %s to get %s on %s',
                         motor, pos1[0], mot_target, goal, imager)
            yield from mv(motor, mot_target)
            logger.debug('reached motor=%s, yag=%s',
                         motor.position, imager.detector.centroid_x)
            raise RecoverDone()
        return recover_plan

    def choose_recover(imagers, ranges):
        def choice():
            assert True
            for n, (i, r) in enumerate(zip(imagers, ranges)):
                if i.position == "OUT":
                    continue
                elif not r[0] <= i.detector.centroid_x <= r[1]:
                    logger.debug('imager %s at %s, not within %s',
                                 i, i.detector.centroid_x, r)
                    return n
                else:
                    return None
            return None
        return choice

    tmo = 5
    plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x', 'pitch',
                     [goal1, goal2], first_steps=step, tolerances=2,
                     averages=1, timeout=tmo)
    #RE(run_wrapper(plan))
    RE(plan)
    y1.move_in()
    y2.move_in()
    assert np.isclose(y1.detector.centroid_x, 480 - goal1, atol=2)
    assert np.isclose(y2.detector.centroid_x, 480 - goal2, atol=2)
