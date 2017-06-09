############
# Standard #
############
import os
import logging

###############
# Third Party #
###############
import pytest
from bluesky import RunEngine
from bluesky.tests.utils import MsgCollector

##########
# Module #
##########
from pswalker.examples import YAG, Mirror, Source, patch_yags
from .utils import FakePath

logfile = os.path.join(os.path.dirname(__file__), "log.txt")
logging.basicConfig(level=logging.DEBUG, filename=logfile,
                    format='%(asctime)s - %(levelname)s ' +
                           '- %(name)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("pytest start")
run_engine_logger = logging.getLogger("RunEngine")


@pytest.fixture(scope='function')
def RE():
    """
    Standard logging runengine
    """
    RE = RunEngine({})
    collector = MsgCollector(msg_hook=run_engine_logger.debug)
    RE.msg_hook = collector
    return RE


@pytest.fixture(scope='function')
def simple_two_bounce_system():
    """
    Simple system that consists of a source and two mirrors.
    """
    s = Source('test_source', 0, 0)
    m1 = Mirror('test_mirror_1', 0, 10, 0)
    m2 = Mirror('test_mirror_2', 5, 20, 0)
    return s, m1, m2


@pytest.fixture(scope='function')
def one_bounce_system():
    """
    Generic single bounce system consisting one mirror with a linear
    relationship with YAG centroid
    """
    s = Source('test_source', 0, 0)
    mot = Mirror('mirror', 0, 50, 0)
    det = YAG('yag', 0, 60, pix=(500,500))
    det = patch_yags(det, mot)
    return s, mot, det


@pytest.fixture(scope='function')
def fake_path_two_bounce():
    """
    pswalker-compatible lightpath.BeamPath with fake objects. Pretends to be
    the HOMS system.
    """
    
    p1h = YAG("p1h", 0, 0)
    feem1 = Mirror("feem1", 0, 10, 0)
    p2h = YAG("p2h", 0, 20)
    feem2 = Mirror("feem2", 0, 30, 0)
    p3h = YAG("p3h", 0, 40)
    hx2_pim = YAG("hx2_pim", 0, 50)
    um6_pim = YAG("um6_pim", 0, 60)
    dg3_pim = YAG("dg3_pim", 0, 70)

    yags = [p1h, p2h, hx2_pim, um6_pim, dg3_pim]
    p1h, p2h, hx2_pim, um6_pim, dg3_pim = patch_yags(yags, [feem1, feem2])
    
    path = FakePath(p1h, feem1, p2h, feem2, p3h, hx2_pim, um6_pim, dg3_pim)
    return path


@pytest.fixture(scope='function')
def fake_yags(fake_path_two_bounce):
    path = fake_path_two_bounce
    yags = [d for d in path.devices if isinstance(d, YAG)]

    # Pretend that the correct values are the current values
    ans = [y.read()['centroid_x']['value'] for y in yags]

    return yags, ans


@pytest.fixture(scope='function')
def lcls_two_bounce_system():
    """
    Simple system that consists of a source, two mirrors, and two imagers.
    """
    s = Source('test_undulator', 0, 0)
    m1 = Mirror('test_m1h', 0, 90.510, 0.0014)
    m2 = Mirror('test_m2h', 0.0317324, 101.843, 0.0014)
    y1 = YAG('test_p3h', 0.0317324, 103.660)
    y2 = YAG('test_dg3', 0.0317324, 375.000)    

    patch_yags([y1, y2], mirrors=[m1, m2], source=s)

    return s, m1, m2, y1, y2
