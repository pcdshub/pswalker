############
# Standard #
############

###############
# Third Party #
###############
import pytest
from bluesky import RunEngine
from bluesky.plans import run_wrapper
from bluesky.callbacks import collector

##########
# Module #
##########
from pswalker.plans import measure_centroid

def test_measure_centroid(one_bounce_system):
    #Only det for this test
    mot, det = one_bounce_system

    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print
    centroids   = []
    col = collector('centroid', centroids)

    #Measure the centroid
    plan = run_wrapper(measure_centroid(det, average=5))
    RE(plan, subs={'event' : col})
    assert centroids == [0., 0., 0., 0., 0.]
