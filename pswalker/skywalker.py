#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import numpy as np
from bluesky import RunEngine
from bluesky.plans import checkpoint, plan_mutator, null

from .plan_stubs import recover_threshold
from .suspenders import (BeamEnergySuspendFloor, BeamRateSuspendFloor,
                         PvAlarmSuspend)
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

    is_branching = False

    def branch_handler(msg):
        nonlocal is_branching
        if not is_branching and msg.command == branch_msg:
            is_branching = True

            def new_gen():
                if branch_choice() is not None:
                    yield from checkpoint()
                    yield from do_branch()
                    logger.debug("Resuming plan after branch")
                yield msg
                nonlocal is_branching
                is_branching = False

            return new_gen(), None
        else:
            return None, None

    brancher = plan_mutator(plan, branch_handler)
    return (yield from brancher)


def lcls_RE(alarming_pvs=None, RE=None):
    """
    Instantiate a run engine that pauses when the lcls beam has problems, and
    optionally when various PVs enter a MAJOR alarm state.

    Parameters
    ----------
    alarming_pvs: list of str, optional
        If provided, we'll suspend the run engine when any of these PVs report
        a MAJOR alarm state.

    RE: RunEngine, optional
        If provided, we'll add suspenders to and return the provided RunEngine
        instead of creating a new one.

    Returns
    -------
    RE: RunEngine
    """
    RE = RE or RunEngine({})
    RE.install_suspender(BeamEnergySuspendFloor(0))
    RE.install_suspender(BeamRateSuspendFloor(0))
    alarming_pvs = alarming_pvs or []
    for pv in alarming_pvs:
        RE.install_suspender(PvAlarmSuspend(pv, "MAJOR"))
    return RE


def homs_RE():
    """
    Instantiate an lcls_RE with the correct alarming pvs and a suspender for
    lightpath blockage.

    Returns
    -------
    RE: RunEngine
    """
    # TODO determine what the correct alarm pvs even are
    # TODO include lightpath suspender
    return lcls_RE()


def homs_system():
    """
    Instantiate the real mirror and yag objects from the real homs system, and
    pack them into a dictionary.

    Returns
    -------
    system: dict
    """
    system = {}
    system['m1h'] = 'm1h'
    system['m2h'] = 'm2h'
    system['hx2'] = 'hx2'
    system['dg3'] = 'dg3'
    system['y1'] = system['hx2']
    system['y2'] = system['dg3']
    return system


def get_thresh_signal(yag):
    """
    Given a yag object, return the signal we'll be using to determine if the
    yag has beam on it.
    """
    return yag.stats.mean_value


def make_homs_recover(yag, motor, threshold):
    """
    Make a recovery plan for a particular yag/motor combination in the homs
    system.
    """
    def homs_recover():
        sig = get_thresh_signal(yag)
        dir_init = np.sign(motor.position) or 1
        plan = recover_threshold(sig, threshold, motor, dir_init, timeout=10)
        return (yield from plan)
    return homs_recover


def make_pick_recover(yag1, yag2, threshold):
    """
    Make a function of zero arguments that will determine if a recovery plan
    needs to be run, and if so, which plan to use.
    """
    def pick_recover():
        if yag1.position == "IN":
            sig = get_thresh_signal(yag1)
            if sig.value < threshold:
                return 0
            else:
                return None
        elif yag2.position == "IN":
            sig = get_thresh_signal(yag2)
            if sig.value < threshold:
                return 1
            else:
                return None
    return pick_recover


def skywalker(detectors, motors, goals,
              gradients=None, tolerances=20, averages=20, timeout=600,
              branches=None, branch_choice=lambda: None):
    """
    Iterwalk as a base, with arguments for branching
    """
    walk = iterwalk(detectors, motors, goals, gradients=gradients,
                    tolerances=tolerances, averages=averages, timeout=timeout)
    # TODO this is where we change detector fields?
    return (yield from branching_plan(walk, branches, branch_choice))


def homs_skywalker(goals, y1='y1', y2='y2', gradients=None, tolerances=20,
                   averages=20, timeout=600, has_beam_floor=30):
    """
    Skywalker with homs-specific devices and recovery methods
    """
    system = homs_system()
    if isinstance(y1, str):
        y1 = system[y1]
    if isinstance(y2, str):
        y2 = system[y2]
    m1h = system['m1h']
    m2h = system['m2h']
    recover_m1 = make_homs_recover(y1, m1h, has_beam_floor)
    recover_m2 = make_homs_recover(y2, m2h, has_beam_floor)
    choice = make_pick_recover(y1, y2, has_beam_floor)
    letsgo = skywalker([y1, y2], [m1h, m2h], goals, gradients=gradients,
                       tolerances=tolerances, averages=averages,
                       timeout=timeout, branches=[recover_m1, recover_m2],
                       branch_choice=choice)
    # TODO or maybe this is where we change detector fields?
    return (yield from letsgo)


def run_homs_skywalker(goals, y1='y1', y2='y2', gradients=None, tolerances=20,
                       averages=20, timeout=600, has_beam_floor=30):
    RE = homs_RE()
    walk = homs_skywalker(goals, y1=y1, y2=y2, gradients=gradients,
                          tolerances=tolerances,
                          averages=averages, timeout=timeout,
                          has_beam_floor=has_beam_floor)
    RE(walk)
