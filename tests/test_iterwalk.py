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
# from bluesky.callbacks   import collector
# from bluesky.tests.utils import MsgCollector
##########
# Module #
##########
from pswalker.iterwalk import iterwalk

TOL = 5

def test_iterwalk_terminates_on_convergence(lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2

    # Goal

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], center_pix, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerences=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None, sort='z'))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], center_pix[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], center_pix[0], atol=TOL)
                       
def test_iterwalk_converges_on_same_side_goal_pixels(lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2

    # Goal pixels both to the right of center
    goal = [p + 300 for p in center_pix]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], center_pix, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerences=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None, sort='z'))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)
                           
    # Goal pixels both to the left of center
    goal = [p - 300 for p in center_pix]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], center_pix, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerences=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None, sort='z'))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)

def test_iterwalk_converges_on_alternate_side_goal_pixels(lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2

    # Goal pixels one to the right and one to the left
    goal = [c + p for c,p in zip(center_pix, [200, -200])]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], center_pix, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerences=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None, sort='z'))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)
                           
    # Goal pixels one to the left and one to the right
    goal = [c + p for c,p in zip(center_pix, [-200, 200])]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], center_pix, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerences=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None, sort='z'))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)
    
