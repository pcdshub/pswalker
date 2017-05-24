#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import numpy as np
from bluesky.plans import checkpoint, plan_mutator, null

from .plan_stubs import recover_threshold
from .suspenders import (BeamEnergySuspendFloor, BeamRateSuspendFloor,
                         PvAlarmSuspend, LightpathSuspender)
from .iterwalk import iterwalk

logger = logging.getLogger(__name__)


def branching_plan(plan, branches, branch_choice, branch_msg='checkpoint'):
    """
    Plan that allows deviations from the original plan at checkpoints.

    Parameters
    ----------
    plan: iterable
        Iterable that returns Msg objects as in a Bluesky plan

    branches: list of functions
        Functions that return valid plans. These are the deviations we may take
        when plan yields a checkpoint.

    branch_choice: function
        Function that tells us which branch to take. This must return None when
        we want to continue to normal plan and an integer that matches an index
        in branches when we want to deviate.

    branch_msg: str, optional
        Which message to branch on. By default, this is checkpoint.
    """
    def do_branch():
        choice = branch_choice()
        if choice is None:
            yield null()
        else:
            branch = branches[choice]
            logger.debug("Switching to branch %s", choice)
            yield from branch()

    def branch_handler(msg):
        if msg.cmd == branch_msg:
            def new_gen():
                if branch_choice() is not None:
                    yield from checkpoint()
                    yield from do_branch()
                    logger.debug("Resuming plan after branch")
                yield msg
            return new_gen(), None
        else:
            return None, None

    plan = plan_mutator(plan, branch_handler)
    return (yield from plan)


def lcls_RE(alarming_pvs=None, RE=None):
    """
    Instantiate a run engine that pauses when the beam has problems.
    """
    RE = RE or RunEngine({})
    RE.install_suspender(BeamEnergySuspendFloor)
    RE.install_suspender(BeamRateSuspendFloor)
    alarming_pvs = alarming_pvs or []
    for pv in alarming_pvs:
        RE.install_suspender(PvAlarmSuspend(pv, "MAJOR"))
    return RE


def homs_RE():
    """
    Instantiate an lcls_RE with the correct alarming pvs.
    """
    return lcls_RE()


def homs_system():
    system = {}
    system['m1h'] = 'm1h'
    system['m2h'] = 'm2h'
    system['y1'] = 'sb1'
    system['y2'] = 'dg3'
    return system


def make_homs_recover(yag, motor, threshold):
    def homs_recover():
        sig = yag.stats.mean_value
        dir_init = np.sign(motor.position) or 1
        plan = recover_threshold(sig, threshold, motor, dir_init, timeout=10)
        return (yield from plan)
    return homs_recover


def pick_recover(yag1, yag2):
    pass


def skywalker(detectors, motors, goals,
              gradients=None, tolerances=20, averages=20, timeout=600,
              branches=None, branch_choice=lambda: None):
    walk = iterwalk(detectors, motors, goals, gradients=gradients,
                    tolerances=tolerances, averages=averages, timeout=timeout)
    # TODO this is where we change detector fields?
    return (yield from branching_plan(walk, branches, branch_choice))


def homs_skywalker(goals, gradients=None, tolerances=20, averages=20,
                   timeout=600, has_beam_floor=30):
    system = homs_system()
    recover_m1 = make_homs_recover(system['y1'], system['m1h'], has_beam_floor)
    recover_m2 = make_homs_recover(system['y2'], system['m2h'], has_beam_floor)
    branch_choice = make_choice
    letsgo = skywalker([system['y1'], system['y2']],
                       [system['m1h'], system['m2h']],
                       goals, gradients=gradients, tolerances=tolerances,
                       averages=averages, timeout=timeout,
                       branches=[recover_m1, recover_m2],
                       branch_choice=branch_choice)
    # TODO or maybe this is where we change detector fields?
    return (yield from letsgo)


def run_homs_skywalker(goals, gradients=None, tolerances=20, averages=20,
                       timeout=600):
    RE = homs_RE()
    walk = homs_skywalker(goals, gradients=gradients, tolerances=tolerances,
                          averages=averages, timeout=timeout)
    RE(walk)
