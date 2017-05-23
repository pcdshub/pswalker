############
# Standard #
############
import logging
###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky             import Msg, RunEngine
from bluesky.plans       import run_wrapper
# from bluesky.callbacks   import collector
# from bluesky.tests.utils import MsgCollector
from ophyd.status import Status
##########
# Module #
##########
from pswalker.iterwalk import iterwalk

TOL = 5
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def test_iterwalk_terminates_on_convergence(lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], center_pix, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
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

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)
                           
    # Goal pixels both to the left of center
    goal = [p - 300 for p in center_pix]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
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

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)
                           
    # Goal pixels one to the left and one to the right
    goal = [c + p for c,p in zip(center_pix, [-200, 200])]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0], atol=TOL)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1], atol=TOL)

def test_iterwalk_raises_RunTimeError_on_motion_timeout(lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2

    # Define a bad set command
    def bad_set(yag, cmd=None, **kwargs):
        logger.info("{0}Setting Attributes. (BAD)".format(yag.log_pref))
        logger.debug("{0}Setting: CMD:{1}, {2} (BAD)".format(
                yag.log_pref, cmd, kwargs))
        return Status(done=True, success=True)
    # Patch yag set command
    y1.set = lambda cmd, **kwargs: bad_set(y1, cmd, **kwargs)

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RunTimeError):
        RE(plan)

    # Reload system
    s, m1, m2, y1, y2 = lcls_two_bounce_system        
    # Patch yag set command
    y2.set = lambda cmd, **kwargs: bad_set(y2, cmd, **kwargs)

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RunTimeError):
        RE(plan)
        
def test_iterwalk_raises_RunTimeError_on_failed_walk_to_pixel(lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    #Create test RunEngine
    RE = RunEngine()
    RE.msg_hook = print

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2

    # Define a bad set command
    def bad_set(mirror, cmd=None, **kwargs):
        logger.info("{0}Setting Attributes. (BAD)".format(mirror.log_pref))
        logger.debug("{0}Setting: CMD:{1}, {2} (BAD)".format(
                mirror.log_pref, cmd, kwargs))
        if cmd in ("IN", "OUT"):
            pass  # If these were removable we'd implement it here
        elif cmd is not None:
            # Here is where we move the pitch motor if a value is set
            mirror._alpha = cmd
            return mirror.alpha.set(cmd)
        mirror._x = kwargs.get('x', mirror._x)
        mirror._z = kwargs.get('z', mirror._z)
        mirror._alpha = kwargs.get('alpha', mirror._alpha)
        for motor in mirror.motors:
            motor_params = motor.read()            
            for key in kwargs.keys():
                if key in motor_params:
                    # Add error term to sets
                    motor.set(kwargs[key] + 0.1)
        return Status(done=True, success=True)
    # Patch yag set command
    m1.set = lambda cmd, **kwargs: bad_set(m1, cmd, **kwargs)

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=20, system=None, averages=None,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RunTimeError):
        RE(plan)        
        
