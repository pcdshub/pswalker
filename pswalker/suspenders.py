#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from enum import Enum
import threading

import numpy as np
from ophyd.utils import ReadOnlyError
from bluesky.plan_stubs import null
from bluesky.suspenders import (SuspenderBase, SuspendCeil, SuspendFloor,
                                SuspendBoolHigh)
# from pcdsdevices.signal import Signal
from ophyd.signal import Signal
# from pcdsdevices.epics.signal import EpicsSignalRO
from ophyd.signal import EpicsSignalRO

from .path import get_path, _controller

logger = logging.getLogger(__name__)


class AvgSignal(Signal):
    """
    Signal that acts as a rolling average of another signal
    """
    def __init__(self, signal, averages, name=None, parent=None, **kwargs):
        super().__init__(name=name, parent=parent, **kwargs)
        self.sig = signal
        self.lock = threading.RLock()
        self.index = 0
        self.values = np.ones(averages) * self.sig.get()
        self.sig.subscribe(self._update_avg)

    def _update_avg(self, *args, value, **kwargs):
        with self.lock:
            self.values[self.index] = value
            self.index += 1
            if self.index == len(self.values):
                self.index = 0
            self.put(np.mean(self.values))


class PvSuspenderBase(SuspenderBase):
    """
    Base class for a suspender that expects a pvname instead of a signal.

    If averages is greater than 1, we'll implement a rolling average of the
    signal instead of the raw value.
    """
    def __init__(self, pvname, sleep=0, pre_plan=None, post_plan=None,
                 tripped_message="", averages=1, **kwargs):
        sig = EpicsSignalRO(pvname)
        if averages > 1:
            sig = AvgSignal(sig, averages, name=sig.name + "_avg")

        def pre_plan(*args, **kwargs):
            logger.debug("starting suspender")
            return (yield from null())

        def post_plan(*args, **kwargs):
            logger.debug("releasing suspender")
            return (yield from null())

        super().__init__(sig, sleep=sleep, pre_plan=pre_plan(),
                         post_plan=post_plan(), tripped_message=tripped_message,
                         **kwargs)


class EnumSuspenderBase(SuspenderBase):
    """
    Base class for interpreting an enum signal by the enumerated names.
    """
    enum = None

    def get_enum(self, enum_state):
        """
        Given an enumerated state string, return the associated enum number.
        """
        return self.enum[enum_state].value


class PvSuspendFloor(SuspendFloor, PvSuspenderBase):
    """
    Suspend the run if a pv falls below a set value.
    """
    pass


class PvSuspendCeil(SuspendCeil, PvSuspenderBase):
    """
    Suspend the run if a pv rises above a set value.
    """
    pass


class BeamEnergySuspendFloor(PvSuspendFloor):
    """
    Suspend the run if the beam energy falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=5.0,
                 pre_plan=None, post_plan=None, averages=120,
                 **kwargs):
        super().__init__("GDET:FEE1:241:ENRC", suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan,
                         averages=averages, **kwargs)


class BeamRateSuspendFloor(PvSuspendFloor):
    """
    Suspend the run if the beam rate falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=5.0,
                 pre_plan=None, post_plan=None, **kwargs):
        super().__init__("EVNT:SYS0:1:LCLSBEAMRATE", suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan, **kwargs)


class FeeSpecSuspendFloor(PvSuspendFloor):
    """
    Suspend the run if the fee spec rate falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=0,
                 pre_plan=None, post_plan=None, **kwargs):
        super().__init__("CAMR:FEE1:441:ArrayRate_RBV", suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan, **kwargs)


class PathSignal(Signal):
    """
    Signal to connect to a lightpath.LightController instance and report the
    number of blocking devices along the desired path.
    """
    def __init__(self, device, exclude=None, path=None,
                 controller=_controller):
        """
        See `LightpathSuspender` for argument documentation.
        """
        self.path = get_path(device, exclude=exclude, path=path,
                             controller=controller)
        self.path.subscribe(self.path_cb, event_type=path.SUB_PTH_CHNG)
        super().__init__(name="lightpath_block_count")

    def get(self, *args, **kwargs):
        """
        Return the number of blocking devices along the loaded path.
        """
        return len(self.path.blocking_devices)

    def put(self, *args, **kwargs):
        raise ReadOnlyError("Cannot put to PathSignal")

    def path_cb(self, *args, **kwargs):
        """
        Update our subscribers with the new number of blocking devices.
        """
        self._run_subs(sub_type=self._default_sub, value=self.get())


class LightpathSuspender(SuspendBoolHigh):
    """
    Suspend the scan if lightpath reports a blockage.
    """
    def __init__(self, device, exclude=None, sleep=0, pre_plan=None,
                 post_plan=None, path=None, controller=_controller):
        """
        Parameters
        ----------
        device: object with "name" attribute.
            The last device in our desired path. Must be a valid argument to
            get_path.

        exclude: list of objects with "name" attributes, optional
            Devices to not consider in the blocking calculation. These should
            also be valid arguments for the "device" parameter.

        sleep: float, optional
            How long to wait in seconds once the path is clear before resuming
            the scan. Defaults to 0.

        pre-plan: iterable or iterator, optional

        post-plan: iterable or iterator, optional

        path: lightpath.BeamPath, optional
            If provided, we'll ignore device and controller arguments and use
            a copy of the provided path. If this is a test/fake path, it must
            be a valid argument to get_path.

        controller: lightpath.LightController, optional
            The controller object that knows about all the paths. If not
            provided, we'll use the global controller that connects to the
            database. If using a test/fake controller, it must be a valid
            argument to get_path.
        """
        path = PathSignal(device, exclude=exclude, path=path,
                          controller=controller)
        super().__init__(path, sleep=sleep, pre_plan=pre_plan,
                         post_plan=post_plan,
                         tripped_message="Lightpath is blocked!")
        self.path_signal = path

    def get_current_lightpath(self):
        return self.path_signal.path


class PvAlarmSuspend(PvSuspendCeil, PvSuspenderBase, EnumSuspenderBase):
    """
    Suspend if .SEVR field reaches or exceeds a chosen alarm state.
    """
    enum = Enum("SevrEnum", "NO_ALARM MINOR MAJOR INVALID")

    def __init__(self, pvname, suspend_enum, sleep=0, pre_plan=None,
                 post_plan=None, **kwargs):
        """
        suspend enum one of MINOR, MAJOR, INVALID.
        """
        if ".SEVR" not in pvname:
            pvname += ".SEVR"
        if suspend_enum == "NO_ALARM":
            raise TypeError("suspend_enum=NO_ALARM would always supsend.")
        if suspend_enum not in ("MINOR", "MAJOR", "INVALID"):
            raise TypeError("suspend enum must be MINOR, MAJOR, or INVALID")
        thresh = self.get_enum(suspend_enum) - 1
        super().__init__(pvname, thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan, **kwargs)
