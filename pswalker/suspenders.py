#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bluesky.suspenders import SuspendFloor
from pcdsdevices.epics.signal import EpicsSignalRO

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
