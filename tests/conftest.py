############
# Standard #
############

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pswalker.examples import YAG, Mirror

@pytest.fixture(scope='function')
def one_bounce_system():
    """
    Generic single bounce system consisting one mirror with a linear
    relationship with YAG centroid
    """
    mv  = Mirror('mirror', 0)
    yag = YAG('yag', mv, 'motor', 100.0)
    return mv, yag

