#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from bluesky import RunEngine
from bluesky.preprocessors import run_decorator, stage_decorator

from .recovery import homs_recovery, sim_recovery
from .suspenders import BeamEnergySuspendFloor, BeamRateSuspendFloor
from .iterwalk import iterwalk
from .utils.argutils import as_list
from .utils import field_prepend

logger = logging.getLogger(__name__)


def lcls_RE(RE=None):
    """
    Instantiate a run engine that pauses when the lcls beam has problems.

    Parameters
    ----------
    RE: RunEngine, optional
        If provided, we'll add suspenders to and return the provided RunEngine
        instead of creating a new one.

    Returns
    -------
    RE: RunEngine
    """
    RE = RE or RunEngine({})
    RE.install_suspender(BeamEnergySuspendFloor(0.5, sleep=5, averages=100))
    RE.install_suspender(BeamRateSuspendFloor(1, sleep=5))
    return RE


def skywalker(detectors, motors, det_fields, mot_fields, goals,
              first_steps=1,
              gradients=None, tolerances=20, averages=20, timeout=600,
              sim=False, use_filters=True, md=None, tol_scaling=None,
              extra_stage=None):
    """
    Iterwalk as a base, with recovery plans, filters, and bonus staging.
    """
    _md = {'goals'     : goals,
           'detectors' : [det.name for det in as_list(detectors)],
           'mirrors'   : [mot.name for mot in as_list(motors)],
           'plan_name' : 'homs_skywalker',
           'plan_args' : dict(goals=goals, gradients=gradients,
                              tolerances=tolerances, averages=averages,
                              timeout=timeout, det_fields=as_list(det_fields),
                              mot_fields=as_list(mot_fields),
                              first_steps=first_steps,tol_scaling=tol_scaling)
          }
    _md.update(md or {})
    goals = [480 - g for g in goals]
    det_fields = as_list(det_fields, length=len(detectors))
    if use_filters:
        filters = []
        for det, fld in zip(detectors, det_fields):
            filters.append({field_prepend(fld, det): lambda x: x > 0})
    else:
        # Don't filter on sims unless testing recovery
        filters = None
    if sim:
        recovery_plan = sim_recovery
    else:
        recovery_plan = homs_recovery

    area_detectors = [det.detector for det in as_list(detectors)]
    to_stage = as_list(motors) + area_detectors

    if extra_stage is not None:
        for dev in extra_stage:
            to_stage.append(dev)

    @run_decorator(md=_md)
    @stage_decorator(to_stage)
    def letsgo():
        walk = iterwalk(detectors, motors, goals, first_steps=first_steps,
                        gradients=gradients,
                        tolerances=tolerances, averages=averages, timeout=timeout,
                        detector_fields=det_fields, motor_fields=mot_fields,
                        system=detectors + motors, recovery_plan=recovery_plan,
                        filters=filters,tol_scaling=tol_scaling)
        return (yield from walk)

    return (yield from letsgo())
