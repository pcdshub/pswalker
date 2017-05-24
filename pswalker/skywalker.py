#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

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
        if branch_choice() is None:
            yield null()
        else:
            branch = branches[branch_choice()]
            yield from branch()

    def branch_handler(msg):
        if msg.cmd == branch_msg:
            def new_gen():
                if branch_choice() is not None:
                    yield from checkpoint()
                    yield from do_branch()
                yield msg
            return new_gen(), None

    plan = plan_mutator(plan, branch_handler)
    return (yield from plan)


def lcls_RE(alarming_pvs=None):
    """
    Instantiate a run engine that pauses when the beam has problems.
    """
    RE = RunEngine({})
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


def skywalker_basic():
    return(yield from branching_plan(iterwalk, [], lambda: None))


def skywalker_model():
    pass


skywalker = skywalker_basic


def run_skywalker():
    """
    THIS IS IT
    """
    RE = homs_RE()
    RE(skywalker)
