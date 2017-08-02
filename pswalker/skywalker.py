#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from bluesky import RunEngine
from bluesky.plans import run_decorator
from bluesky.callbacks import LiveTable
from pcdsdevices.epics.pim import PIM
from pcdsdevices.epics.mirror import OffsetMirror

from .plan_stubs import prep_img_motors
from .recovery import homs_recovery
from .suspenders import (BeamEnergySuspendFloor, BeamRateSuspendFloor,
                         PvAlarmSuspend, LightpathSuspender)
from .iterwalk import iterwalk
from .utils.argutils import as_list
from .utils import field_prepend

logger = logging.getLogger(__name__)


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
    RE.install_suspender(BeamEnergySuspendFloor(0.01))
    RE.install_suspender(BeamRateSuspendFloor(2))
    alarming_pvs = alarming_pvs or []
    for pv in alarming_pvs:
        RE.install_suspender(PvAlarmSuspend(pv, "MAJOR"))
    RE.msg_hook = RE.log.debug
    return RE


def homs_RE():
    """
    Instantiate an lcls_RE with the correct alarming pvs and a suspender for
    lightpath blockage.

    Returns
    -------
    RE: RunEngine
    """
    RE = lcls_RE()
    # TODO determine what the correct alarm pvs even are
    # TODO include lightpath suspender
    return RE


def skywalker(detectors, motors, det_fields, mot_fields, goals,
              first_steps=1,
              gradients=None, tolerances=20, averages=20, timeout=600,
              branches=None, branch_choice=lambda: None, md=None):
    """
    Iterwalk as a base, with arguments for branching
    """
    _md = {'goals'     : goals,
           'detectors' : [det.name for det in as_list(detectors)],
           'mirrors'   : [mot.name for mot in as_list(motors)],
           'plan_name' : 'homs_skywalker',
           'plan_args' : dict(goals=goals, gradients=gradients,
                              tolerances=tolerances, averages=averages,
                              timeout=timeout, det_fields=as_list(det_fields),
                              mot_fields=as_list(mot_fields),
                              first_steps=first_steps)
          }
    _md.update(md or {})
    goals = [480 - g for g in goals]
    filters = {}
    for det, fld in zip(detectors, det_fields):
        filters[field_prepend(fld, det)] = lambda x: x > 0

    @run_decorator(md=_md)
    def letsgo():
        walk = iterwalk(detectors, motors, goals, first_steps=first_steps,
                        gradients=gradients,
                        tolerances=tolerances, averages=averages, timeout=timeout,
                        detector_fields=det_fields, motor_fields=mot_fields,
                        system=detectors + motors, recovery_plan=homs_recovery,
                        filters=filters)
        return (yield from walk)


    return (yield from letsgo())

def get_lightpath_suspender(yags):
    # TODO initialize lightpath
    # Make the suspender to go to the last yag and exclude prev yags
    return LightpathSuspender(yags[-1], exclude=yags[:-1])
