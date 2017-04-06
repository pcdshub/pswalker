
from pswalker.cnc import CNC
from pswalker.models.templates.model_two_flat_tilted_mirrors_two_imagers import (
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
    m.p1 = None
    m.p2 = None
    return m

def test_cnc_instantiates():
    assert CNC()

def test_correct_model_loaded():
    test_model = get_model()
    cnc = CNC()
    model = builder.load("test_model")

    assert test_model.source.x == model.source.x
    assert test_model.source.xp == model.source.xp
    assert test_model.mirror_1.z == model.mirror_1.z
    assert test_model.mirror_2.z == model.mirror_2.z
    assert test_model.imager_1.z == model.imager_1.z
    assert test_model.imager_2.z == model.imager_2.z
    assert test_model.mirror_1.x == model.mirror_1.x
    assert test_model.mirror_2.x == model.mirror_2.x
    assert test_model.imager_1.x == model.imager_1.x
    assert test_model.imager_2.x == model.imager_2.x
    assert test_model.imager_1.image_xsz == model.imager_1.image_xsz
    assert test_model.imager_1.mppix == model.imager_1.mppix
    assert test_model.imager_2.image_xsz == model.imager_2.image_xsz
    assert test_model.imager_2.mppix == model.imager_2.mppix
    assert test_model.p1 == model.p1
    assert test_model.p2 == model.p2
