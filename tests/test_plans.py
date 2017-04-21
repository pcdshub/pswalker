############
# Standard #
############

###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky             import Msg, RunEngine
from bluesky.plans       import run_wrapper
from bluesky.callbacks   import collector
from bluesky.tests.utils import MsgCollector
##########
# Module #
##########
from pswalker.plans import measure_average, measure_centroid, walk_to_pixel

def test_measure_average(one_bounce_system):
    #Load motor and yag
    mot, det = one_bounce_system

    #Create test RunEngine
    RE   = RunEngine()
    hook = MsgCollector(msg_hook=print)
    RE.msg_hook = hook
    #Fake event storage 
    centroids = []
    readbacks = []
    col_c = collector('centroid', centroids)
    col_r = collector('motor',    readbacks)
    #Run plan
    RE(run_wrapper(measure_average([det, mot],
                                   ['centroid','motor'],
                                   delay=0.1, num=5)),
       subs={'event':[col_c, col_r]})
    #Check events
    assert centroids == [0.,0.,0.,0.,0.]
    assert readbacks == [0.,0.,0.,0.,0.]

    #Clear from last test
    centroids.clear()
    readbacks.clear()
    #Run with array of delays
    RE(run_wrapper(measure_average([det, mot],
                                   ['centroid','motor'],
                                   delay=[0.1], num=2)),
       subs={'event':[col_c, col_r]})
    #Check events
    assert centroids == [0., 0.]
    assert readbacks == [0., 0.]

    #Invalid delay settings
    with pytest.raises(ValueError):
        RE(run_wrapper(measure_average([det, mot],
                                       ['centroid','motor'],
                                       delay=[0.1], num=3)))

def test_measure_centroid(one_bounce_system):
    #Load motor and yag
    mot, det = one_bounce_system
    #Create test RunEngine
    RE   = RunEngine()
    #Fake event storage 
    centroids = []
    col_c = collector('centroid', centroids)
    #Run plan
    RE(run_wrapper(measure_centroid(det, average=5)),
       subs={'event':[col_c]})
    #Check events
    assert centroids == [0.,0.,0.,0.,0.]

def test_walk_to_pixel(one_bounce_system):
    mot, det = one_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    #Walk to the pixel
    plan = run_wrapper(walk_to_pixel(det, mot, 200, 0, first_step=1,
                                     tolerance=10, average=None,
                                     max_steps=3))
    RE(plan)
    assert np.isclose(det.read()['centroid']['value'], 200, atol=10)
