############
# Standard #
############

###############
# Third Party #
###############
import pytest
from lightpath import BeamPath

##########
# Module #
##########
from pswalker.examples import YAG, Mirror
from pswalker.examples import TwoMirrorSystem


@pytest.fixture(scope='function')
def one_bounce_system():
    """
    Generic single bounce system consisting one mirror with a linear
    relationship with YAG centroid
    """
    mv  = Mirror('mirror', 0)
    yag = YAG('yag', mv, 'motor', 100.0)
    return mv, yag


@pytest.fixture(scope='function')
def fake_path_two_bounce():
    """
    pswalker-compatible lightpath.BeamPath with fake objects. Pretends to be
    the HOMS system.
    """
    system = TwoMirrorSystem()
    path = BeamPath(system.mirror_1, system.mirror_2,
                    system.yag_1, system.yag_2)
    return path
