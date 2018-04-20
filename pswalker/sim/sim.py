"""
Simulated device classes
"""
from ophyd.device import Device, Component

from .signal import FakeSignal


class SimDevice(Device):
    """
    Class to house components and methods common to all simulated devices.
    """
    sim_x = Component(FakeSignal, value=0)
    sim_y = Component(FakeSignal, value=0)
    sim_z = Component(FakeSignal, value=0)
