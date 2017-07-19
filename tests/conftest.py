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
from pcdsdevices.sim import source, mirror, pim

##########
# Module #
##########
from pswalker.examples import patch_pims
from .utils import FakePath

#################
# Logging Setup #
#################

#Default logfile
logfile = os.path.join(os.path.dirname(__file__), "log.txt")
#Enable the logging level to be set from the command line
def pytest_addoption(parser):
    parser.addoption("--log", action="store", default="DEBUG",
                     help="Set the level of the log")
    parser.addoption("--logfile", action="store", default=logfile,
                     help="Write the log output to specified file path")

#Create a fixture to automatically instantiate logging setup
@pytest.fixture(scope='session', autouse=True)
def set_level(pytestconfig):
    #Read user input logging level
    log_level = getattr(logging, pytestconfig.getoption('--log'), None)

    #Report invalid logging level
    if not isinstance(log_level, int):
        raise ValueError("Invalid log level : {}".format(log_level))

    #Create basic configuration
    logging.basicConfig(level=log_level,
                        filename=pytestconfig.getoption('--logfile'),
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
    s = source.Undulator('test_source')
    m1 = mirror.OffsetMirror('test_mirror_1', z=10)
    m2 = mirror.OffsetMirror('test_mirror_2', x=5, z=20)
    return s, m1, m2


@pytest.fixture(scope='function')
def one_bounce_system():
    """
    Generic single bounce system consisting one mirror with a linear
    relationship with YAG centroid
    """
    s = source.Undulator('test_source')
    mot = mirror.OffsetMirror('mirror', z=50)
    det = pim.PIM('yag', z=60, size=(500,500))
    det = patch_pims(det, mot)
    return s, mot, det


@pytest.fixture(scope='function')
def fake_path_two_bounce():
    """
    pswalker-compatible lightpath.BeamPath with fake objects. Pretends to be
    the HOMS system.
    """
    
    p1h = pim.PIM("p1h")
    feem1 = mirror.OffsetMirror("feem1", z=10)
    p2h = pim.PIM("p2h", z=20)
    feem2 = mirror.OffsetMirror("feem2", z=30)
    p3h = pim.PIM("p3h", z=40)
    hx2_pim = pim.PIM("hx2_pim", z=50)
    um6_pim = pim.PIM("um6_pim", z=60)
    dg3_pim = pim.PIM("dg3_pim", z=70)

    yags = [p1h, p2h, hx2_pim, um6_pim, dg3_pim]
    p1h, p2h, hx2_pim, um6_pim, dg3_pim = patch_pims(yags, [feem1, feem2])
    
    path = FakePath(p1h, feem1, p2h, feem2, p3h, hx2_pim, um6_pim, dg3_pim)
    return path


@pytest.fixture(scope='function')
def fake_yags(fake_path_two_bounce):
    path = fake_path_two_bounce
    yags = [d for d in path.devices if isinstance(d, pim.PIM)]

    # Pretend that the correct values are the current values
    ans = [y.read()[y.name + '_detector_stats2_centroid_x']['value'] 
           for y in yags]

    return yags, ans


@pytest.fixture(scope='function')
def lcls_two_bounce_system():
    """
    Simple system that consists of a source, two mirrors, and two imagers.
    """
    s = source.Undulator('test_undulator')
    m1 = mirror.OffsetMirror('test_m1h', z=90.510, alpha=0.0014)
    m2 = mirror.OffsetMirror('test_m2h', x=0.0317324, z=101.843, alpha=0.0014)
    y1 = pim.PIM('test_p3h', x=0.0317324, z=103.660)
    y2 = pim.PIM('test_dg3', x=0.0317324, z=375.000)    

    patch_pims([y1, y2], mirrors=[m1, m2], source=s)

    return s, m1, m2, y1, y2
