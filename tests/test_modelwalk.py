# Testing suite for modelwalk

from pswalker.modelwalk import ModelWalker
from pswalker.models.templates.model_two_flat_tilted_mirrors_two_imagers import (
    TwoFlatTiltedMirrorsTwoImagers)

class Walker(object):
    def move_alpha_1(self, alpha):
        print("Moved alpha 1 motor to {0}".format(alpha))
    def move_alpha_2(self, alpha):
        print("Moved alpha 2 motor to {0}".format(alpha))

def get_model(p1, p2):
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
    m.p1 = p1
    m.p2 = p2
    return m

def test_algorithm_correctness_01():
    walker = Walker()
    model = get_model(250, 250)
    modWalker = ModelWalker(walker, model)
    alpha1, alpha2 = modWalker.align()
    assert round(alpha1, 4) == 0.0014
    assert round(alpha2, 4) == 0.0014


def test_algorithm_correctness_02():
    walker = Walker()
    model = get_model(300, 400)
    modWalker = ModelWalker(walker, model)
    alpha1, alpha2 = modWalker.align()
    assert round(alpha1, 10) == round(0.0013644716418, 10)
    assert round(alpha2, 10) == round(0.0013674199723, 10)

def test_algorithm_correctness_03():
    walker = Walker()
    model = get_model(180, 150)
    modWalker = ModelWalker(walker, model)
    alpha1, alpha2 = modWalker.align()
    assert round(alpha1, 10) == round(0.00144856550472, 10)
    assert round(alpha2, 10) == round(0.00144768100557, 10)


