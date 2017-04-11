# Model used for the XRT Ray tracing simulator

from __future__ import absolute_import

from .templates.model_two_flat_tilted_mirrors_two_imagers import (
	TwoFlatTiltedMirrorsTwoImagers)

def get_model():
    m = TwoFlatTiltedMirrorsTwoImagers()
    m.source.x = 0.0
    m.source.xp = 0.0
    m.mirror_1.z = 90.510
    m.mirror_2.z = 101.843
    m.imager_1.z = 103.660
    m.imager_2.z = 375.000
    m.mirror_1.x = 0.0
    m.mirror_2.x = 0.0317324
    m.imager_1.x = 0.0317324
    m.imager_2.x = 0.0317324
    m.imager_1.image_xsz = 500
    m.imager_1.mppix = 0.008/500
    m.imager_2.image_xsz = 500
    m.imager_2.mppix = 0.008/500
    return m
