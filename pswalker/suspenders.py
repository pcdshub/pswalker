#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ophyd.utils import ReadOnlyError
from bluesky.suspenders import SuspenderBase, SuspendFloor, SuspendBoolLow
from pcdsdevices.signal import Signal
from pcdsdevices.epics.signal import EpicsSignalRO

from path import get_path, _controller


class BeamEnergySuspender(SuspendFloor):
    """
    Suspend the run if the beam energy falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=0, pre_plan,
                 post_plan):
        beam_energy = EpicsSignalRO("SIOC:SYS0:ML00:AO627")
        super().__init__(beam_energy, suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan)


class BeamRateSuspender(SuspendFloor):
    """
    Suspend the run if the beam rate falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=0, pre_plan,
                 post_plan):
        beam_rate = EpicsSignalRO("EVNT:SYS0:1:LCLSBEAMRATE")
        super().__init__(beam_rate, suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan)


class PathSignal(Signal):
    def __init__(self, device, controller=_controller):
        self.path = get_path(device, controller=controller)
        self.path.subscribe(self.path_cb, event_type=path.SUB_PTH_CHNG)

    def get(self, *args, **kwargs):
        return len(self.path.blocking_devices)

    def put(self, *args, **kwargs):
        raise ReadOnlyError("Cannot put to PathSignal")

    def path_cb(*args, **kwargs):
        self._run_subs(sub_type=self.SUB_VALUE, value=self.get())


class LightpathSuspender(SuspendBoolLow):
    def __init__(self, device, sleep=0, pre_plan=None, post_plan=None,
                 controller=_controller):
        path = PathSignal(device, controller=controller)
        super().__init__(path, sleep=sleep, pre_plan=pre_plan,
                         post_plan=post_plan,
                         tripped_message="Lightpath is blocked!")
