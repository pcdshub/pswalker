############
# Standard #
############
import logging
###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky.preprocessors import run_wrapper
from ophyd.status import Status
##########
# Module #
##########
from pswalker.iterwalk import iterwalk

TOL = 5
logger = logging.getLogger(__name__)

tmo = 10


@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("goal1", [-300, 0, 300])
@pytest.mark.parametrize("goal2", [-300, 0, 300])
@pytest.mark.parametrize("first_steps", [1e-4])
@pytest.mark.parametrize("gradients", [None])
@pytest.mark.parametrize("tolerances", [3])
@pytest.mark.parametrize("overshoot", [0])
@pytest.mark.parametrize("max_walks", [5])
@pytest.mark.parametrize("tol_scaling", [None,2])
def test_iterwalk(RE, lcls_two_bounce_system,
                  goal1, goal2, first_steps, gradients,
                  tolerances, overshoot, max_walks,tol_scaling):
    logger.debug("test_iterwalk with goal1=%s, goal2=%s, first_steps=%s, " +
                 "gradients=%s, tolerances=%s, overshoot=%.2f, max_walks=%s",
                 goal1, goal2, first_steps, gradients, tolerances, overshoot,
                 max_walks)
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    goal1 += y1.size[0]/2
    goal2 += y2.size[0]/2

    goal = [goal1, goal2]

    plan = run_wrapper(iterwalk([y1, y2], [m1, m2], goal, starts=None,
                                first_steps=first_steps, gradients=gradients,
                                detector_fields='detector_stats2_centroid_x',
                                motor_fields='sim_alpha',
                                tolerances=tolerances, system=[m1, m2, y1, y2],
                                averages=1, overshoot=overshoot,
                                max_walks=max_walks, timeout=None,
                                tol_scaling=tol_scaling))
    RE(plan)
    assert np.isclose(
        y1.read()[y1.name + '_detector_stats2_centroid_x']['value'],
        goal[0],
        atol=tolerances)
    assert np.isclose(
        y2.read()[y2.name + '_detector_stats2_centroid_x']['value'],
        goal[1],
        atol=tolerances)

    # Make sure we actually read all the groups as we went
    m1_reads = 0
    m2_reads = 0
    y1_reads = 0
    y2_reads = 0
    saves = 0
    for msg in RE.msg_hook.msgs:
        if msg.command == 'read':
            if msg.obj == m1:
                m1_reads += 1
            if msg.obj == m2:
                m2_reads += 1
            if msg.obj == y1:
                y1_reads += 1
            if msg.obj == y2:
                y2_reads += 1
        if msg.command == 'save':
            saves += 1
    assert saves > 0
    assert all(map(lambda x: x == saves,
                   [m1_reads, m2_reads, y1_reads, y2_reads]))



@pytest.mark.timeout(tmo)
def test_iterwalk_raises_RuntimeError_on_motion_timeout(RE, lcls_two_bounce_system):
    logger.debug("test_iterwalk_raises_RuntimeError_on_motion_timeout")
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    # Center pixels of yag
    center_pix = [y1.size[0]/2] * 2
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
                                first_steps=1, gradients=None,
                                detector_fields='detector_stats2_centroid_x',
                                motor_fields='sim_alpha',
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
                                detector_fields='detector_stats2_centroid_x',
                                motor_fields='sim_alpha',
                                tolerances=TOL, system=None, averages=1,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RuntimeError):
        RE(plan)
        
def test_iterwalk_raises_RuntimeError_on_failed_walk_to_pixel(RE, lcls_two_bounce_system):
    logger.debug("test_iterwalk_raises_RuntimeError_on_failed_walk_to_pixel")
    s, m1, m2, y1, y2 = lcls_two_bounce_system

    # Center pixels of yag
    center_pix = [y1.size[0]/2] * 2
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
            mirror.sim_pitch = cmd
            return mirror.pitch.set(cmd)
        mirror.sim_x = kwargs.get('x', mirror.sim_x)
        mirror.sim_z = kwargs.get('z', mirror.sim_z)
        mirror.sim_pitch = kwargs.get('pitch', mirror.sim_pitch)
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
                                detector_fields='sim_x',
                                motor_fields='sim_alpha',
                                tolerances=TOL, system=None, averages=1,
                                overshoot=0, max_walks=5, timeout=None))
    # Check a RunTimError is raised
    with pytest.raises(RuntimeError):
        RE(plan)        
        
