#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import pytest
from bluesky.plans import (open_run, close_run, create, read, save, mv,
                           checkpoint)
from pswalker.skywalker import branching_plan
from .utils import collector

logger = logging.getLogger(__name__)


@pytest.mark.timeout(10)
def test_branching_plan(RE, lcls_two_bounce_system):
    logger.debug("test_branching_plan start")
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    reads = []
    m1.parent = None

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

    RE(test_plan(), collector(m1.name + '_alpha', reads))

    assert len(reads) == 10
    assert reads == [0, 1, 2, 3, 4, 5, 0, 1, 2, 3]
