# Scaffold module to write hard coded module classes for the purpose of testing 
# while skywalker is incomplete. It is fully expected that this will disappear
# once each of the components are fleshed out enough that the system can run.

from __future__ import print_function

from modelwalk import ModelWalker
from models.templates.model_two_flat_tilted_mirrors_two_imagers import TwoFlatTiltedMirrorsTwoImagers

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
    m.p1 = p1
    m.p2 = p2
    m.imager_1.image_xsz = 500
    m.imager_1.mppix = 0.008/500
    m.imager_2.image_xsz = 500
    m.imager_2.mppix = 0.008/500
    return m

def test_modelwalk():
    walker = Walker()
    model = get_model(250, 250)

    modWalker = ModelWalker(walker, model)
    alpha1, alpha2 = modWalker.align()
    assert(round(alpha1, 4) == 0.0014)
    assert(round(alpha2, 4) == 0.0014)
    # except:
    # import IPython; IPython.embed()


if __name__ == "__main__":
    test_modelwalk()




