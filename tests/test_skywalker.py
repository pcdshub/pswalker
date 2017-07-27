#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import numpy as np
import pytest
from bluesky.plans import (open_run, close_run, create, read, save, mv,
                           checkpoint, run_wrapper)
from pswalker.skywalker import (branching_plan, skywalker)
from pswalker.utils.exceptions import RecoverDone
from .utils import collector, MotorSignal

logger = logging.getLogger(__name__)


@pytest.mark.timeout(10)
def test_branching_plan(RE, lcls_two_bounce_system):
    logger.debug("test_branching_plan start")
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    reads = []

    class TestException(Exception):
        pass

    def main_plan(det, count):
        yield from open_run()
        for i in range(count):
            yield from create()
            yield from read(det)
            yield from save()
            try:
                yield from checkpoint()
            except TestException:
                yield from mv(det, 0)
        yield from close_run()

    def test_plan():
        yield from mv(m1, 0)
        assert m1.position == 0, 'test init failed'

        plan = main_plan(m1, 10)

        def branch():
            if m1.position < 5:
                return (yield from mv(m1, m1.position + 1))
            else:
                raise TestException()

        def choice():
            if len(reads) > m1.position:
                return 0
            return None

        yield from branching_plan(plan, [branch], choice, 'checkpoint')

    RE(test_plan(), collector(m1.name + '_pitch', reads))

    assert len(reads) == 10
    assert reads == [0, 1, 2, 3, 4, 5, 0, 1, 2, 3]


@pytest.mark.parametrize("use_recover", [False, True])
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
    if use_recover:
        plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x', 'pitch',
                         [goal1, goal2], first_steps=step, tolerances=2,
                         averages=1, timeout=tmo,
                         branches=[recover(m1, y1, range1),
                                   recover(m2, y2, range2)],
                         branch_choice=choose_recover([y1, y2],
                                                      [range1, range2]))
    else:
        plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x', 'pitch',
                         [goal1, goal2], first_steps=step, tolerances=2,
                         averages=1, timeout=tmo)
    #RE(run_wrapper(plan))
    RE(plan)
    y1.move_in()
    y2.move_in()
    assert np.isclose(y1.detector.centroid_x, goal1, atol=2)
    assert np.isclose(y2.detector.centroid_x, goal2, atol=2)
