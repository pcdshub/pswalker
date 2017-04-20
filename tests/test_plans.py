############
# Standard #
############

###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky import RunEngine
from bluesky.plans import run_wrapper
from bluesky.callbacks import collector

##########
# Module #
##########
from pswalker.plans import walk_to_pixel, measure_centroid

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


def test_walk_to_pixel(one_bounce_system):
    mot, det = one_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    #Walk to the pixel
    plan = run_wrapper(walk_to_pixel(det, mot, 200, 0, first_step=1,
                                     tolerance=10, average=None,
                                     timeout=2))
    RE(plan)
    assert np.isclose(det.read()['centroid']['value'], 200, atol=10)
