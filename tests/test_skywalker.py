#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from bluesky.plans import count, mv
from pswalker.skywalker import branching_plan
from .utils import collector


@pytest.mark.timeout(10)
def test_branching_plan(RE, lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    reads = []

    def test_plan():
        yield from mv(m1, 0)
        assert m1.position == 0, 'test init failed'

        plan = count([m1], 10)

        def branch():
            return (yield from mv(m1, m1.position + 1))

        def choice():
            if len(reads) > m1.position:
                return 0
            return None

        yield from branching_plan(plan, [branch], choice, 'checkpoint')

    RE(test_plan(), collector(m1.name + '_alpha', reads))

    assert len(reads) == 10
    assert reads == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
