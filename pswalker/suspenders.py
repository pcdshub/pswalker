#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ophyd.utils import ReadOnlyError
from bluesky.suspenders import SuspenderBase, SuspendFloor, SuspendBoolHigh
# from pcdsdevices.signal import Signal
from ophyd.signal import Signal
# from pcdsdevices.epics.signal import EpicsSignalRO
from ophyd.signal import EpicsSignalRO

from .path import get_path, _controller


class PvSuspenderBase(SuspenderBase):
    """
    Base class for a suspender that expects a pvname instead of a signal.
    """
    def __init__(self, pvname, sleep=0, pre_plan=None, post_plan=None,
                 tripped_message=""):
        sig = EpicsSignalRO(pvname)
        super().__init__(sig, sleep=sleep, pre_plan=pre_plan,
                         post_plan=post_plan, tripped_message=tripped_message)


class PvSuspendFloor(SuspendFloor, PvSuspenderBase):
    """
    Suspend the run if a pv falls below a set value.
    """
    pass


class BeamEnergySuspendFloor(PvSuspendFloor):
    """
    Suspend the run if the beam energy falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=0,
                 pre_plan=None, post_plan=None):
        super().__init__("SIOC:SYS0:ML00:AO627", suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan)


class BeamRateSuspendFloor(PvSuspendFloor):
    """
    Suspend the run if the beam rate falls below a set value.
    """
    def __init__(self, suspend_thresh, resume_thresh=None, sleep=0,
                 pre_plan=None, post_plan=None):
        super().__init__("EVNT:SYS0:1:LCLSBEAMRATE", suspend_thresh,
                         resume_thresh=resume_thresh, sleep=sleep,
                         pre_plan=pre_plan, post_plan=post_plan)


class PathSignal(Signal):
    """
    Signal to connect to a lightpath.LightController instance and report the
    number of blocking devices along the desired path.
    """
    def __init__(self, device, exclude=None, path=None,
                 controller=_controller):
        """
        See `LightPathSuspender` for argument documentation.
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
