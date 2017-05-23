############
# Standard #
############
import logging
###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky.plans import run_wrapper
from ophyd.status import Status
##########
# Module #
##########
from pswalker.iterwalk import iterwalk

TOL = 5
logger = logging.getLogger(__name__)


@pytest.mark.timeout(3)
@pytest.mark.parametrize("goal1", [-300, 0, 300])
@pytest.mark.parametrize("goal2", [-300, 0, 300])
@pytest.mark.parametrize("first_steps", [1e-6])
@pytest.mark.parametrize("gradients", [None])
@pytest.mark.parametrize("tolerances", [3])
@pytest.mark.parametrize("overshoot", [0, 0.25])
@pytest.mark.parametrize("max_walks", [5])
def test_iterwalk(RE, lcls_two_bounce_system,
                  goal1, goal2, first_steps, gradients,
                  tolerances, overshoot, max_walks):
    logger.debug("test_iterwalk with goal1=%s, goal2=%s, first_steps=%s, " +
                 "gradients=%s, tolerances=%s, overshoot=%.2f, max_walks=%s",
                 goal1, goal2, first_steps, gradients, tolerances, overshoot,
                 max_walks)
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    goal1 += y1.pix[0]/2
    goal2 += y2.pix[0]/2

    goal = [goal1, goal2]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=first_steps, gradients=gradients,
                                detector_fields='centroid_x',
                                motor_fields='alpha',
                                tolerances=tolerances, system=None, averages=1,
                                overshoot=overshoot, max_walks=max_walks,
                                timeout=None))
    RE(plan)
    assert np.isclose(y1.read()['centroid_x']['value'], goal[0],
                      atol=tolerances)
    assert np.isclose(y2.read()['centroid_x']['value'], goal[1],
                      atol=tolerances)


@pytest.mark.timeout(3)
def test_iterwalk_raises_RuntimeError_on_motion_timeout(RE, lcls_two_bounce_system):
    logger.debug("test_iterwalk_raises_RuntimeError_on_motion_timeout")
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2
    goal = [p + 300 for p in center_pix]

    # Define a bad set command
    def bad_set(yag, cmd=None, **kwargs):
        logger.info("{0}Setting Attributes. (BAD)".format(yag.log_pref))
        logger.debug("{0}Setting: CMD:{1}, {2} (BAD)".format(
                yag.log_pref, cmd, kwargs))
        return Status(done=True, success=False)
    # Patch yag set command
    y1.set = lambda cmd, **kwargs: bad_set(y1, cmd, **kwargs)

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1e-6, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=TOL, system=None, averages=1,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RuntimeError):
        RE(plan)

    # Reload system
    s, m1, m2, y1, y2 = lcls_two_bounce_system        
    # Patch yag set command
    y2.set = lambda cmd, **kwargs: bad_set(y2, cmd, **kwargs)

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1e-6, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=TOL, system=None, averages=1,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RuntimeError):
        RE(plan)
        
def test_iterwalk_raises_RuntimeError_on_failed_walk_to_pixel(RE, lcls_two_bounce_system):
    logger.debug("test_iterwalk_raises_RuntimeError_on_failed_walk_to_pixel")
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    # Center pixels of yag
    center_pix = [y1.pix[0]/2] * 2
    goal = [p + 300 for p in center_pix]

    # Define a bad set command
    def bad_set(mirror, cmd=None, **kwargs):
        logger.info("{0}Setting Attributes. (BAD)".format(mirror.log_pref))
        logger.debug("{0}Setting: CMD:{1}, {2} (BAD)".format(
                mirror.log_pref, cmd, kwargs))
        err = 0.1
        if cmd in ("IN", "OUT"):
            pass  # If these were removable we'd implement it here
        elif cmd is not None:
            # Here is where we move the pitch motor if a value is set
            cmd += err
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
                    motor.set(kwargs[key] + err)
        return Status(done=True, success=True)
    # Patch yag set command
    m1.set = lambda cmd, **kwargs: bad_set(m1, cmd, **kwargs)

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=1e-6, gradients=None,
                                detector_fields='centroid_x', motor_fields='alpha',
                                tolerances=TOL, system=None, averages=1,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RuntimeError):
        RE(plan)        
        
