from ophyd.areadetector import detectors
from ophyd.device import Component

from .cam import (CamBase, PulnixCam)
from .plugins import (StatsPlugin, ImagePlugin)
from ..signal import FakeSignal


class DetectorBase(detectors.DetectorBase):
    cam = Component(FakeSignal, ":")


class PulnixDetector(DetectorBase):
    cam = Component(PulnixCam, ":")

class SimDetector(detectors.DetectorBase):
    """
    Generic simulated detector that has image, stats and cam components.
    """
    cam = Component(CamBase, ":")
    image = Component(ImagePlugin, ":IMAGE:", read_attrs=["array_data"])
    stats = Component(StatsPlugin, ":Stats:", read_attrs=['centroid',
                                                          'mean_value'])

    def __init__(self, prefix, read_attrs=None, *args, **kwargs):
        if read_attrs is None:
            read_attrs = ["cam", "image", "stats"]
        super().__init__(prefix, read_attrs=read_attrs, *args, **kwargs)
    
    def centroid_x(self):
        return self.stats.centroid.x.value
    
    def centroid_y(self):
        return self.stats.centroid.y.value

    @property
    def centroid(self):
        return (self.centroid_x, self.centroid_y)
    
