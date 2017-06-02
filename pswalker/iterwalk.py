#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import logging

from bluesky.plans import checkpoint

from .plans import walk_to_pixel, measure_centroid
from .plan_stubs import prep_img_motors
from .utils.argutils import as_list

logger = logging.getLogger(__name__)


def iterwalk(detectors, motors, goals, starts=None, first_steps=1,
             gradients=None, detector_fields='centroid_x',
             motor_fields='alpha', tolerances=20, system=None, averages=1,
             overshoot=0, max_walks=None, timeout=None):
    """
    Iteratively adjust a system of detectors and motors where each motor
    primarily affects the reading of a single detector but also affects the
    other axes parasitically.

    This is a Bluesky plan, but it does not have start run or end run
    decorators so it can be included inside of other plans. It yields a
    checkpoint message before adjusting the detector positions and before
    executing a walk substep.

    All list arguments that expect one entry per detector must be the same
    length as the detectors list. If any optional list arguments are provided
    as single values instead of as iterables, iterwalk will interpret it as
    "use this value for every detector".

    Parameters
    ----------
    detectors: list of objects
        These are your axes of motion, which must implement both the Bluesky
        reader interface and the setter interface. The set method must accept
        the "IN" and "OUT" arguments to move the device in and out. It is
        assumed that detectors earlier in the list block detectors later in the
        list.

    motors: list of objects
        These are your axes of motion, which must implement both the Bluesky
        reader interface and the setter interface.

    goals: list of numbers
        These are the scalar readbacks expected from the detectors at the
        desired positions.

    starts: list of numbers, optional
        If provided, these are the nominal positions to move the motors to
        before starting to align.

    first_steps: list of numbers, optional.
        This is how far the motors will be moved in an initial probe step as we
        gauge the detector's response. This argument is ignored if 'gradients'
        is provided.

    gradients: list of numbers, optional
        If provided, this is a guess at the ratio between motor move and change
        in detector readback. This will be used to make a very good first guess
        at the first step towards the goal pixel. This should be in units of
        detector/motor

    detector_fields: list of strings, optional
        For each detector, this is the field we're walking to.

    motor_fields: list of strings, optional
        For each motor, this is the field we're using along with the
        detector_field to build our linear regression. This should be the
        readback with nominally the same value as the position field.

    tolerances: list of numbers, optional
        If our detector readbacks are within these tolerances of the goal
        positions, we'll treat the goal as reached.

    system: list of readable objects, optional
        Other system parameters that we'd like to read during the walk.

    averages: list of numbers, optional
        For each detector, this is the number of shots to average before
        settling on a reading.

    overshoot: number, optional
        The percent to overshoot at each goal step. For these parasitic
        systems, over or undershooting can allow convergence to occur faster.
        An overshoot of 0 is no overshoot, an overshoot of 0.1 is a 10%
        overshoot, an overshoot of -0.2 is a 20% undershoot, etc.

    max_walks: int, optional
        The number of sets of walks to try before giving up on the alignment.
        E.g. if max_walks is 3, we'll move each motor/detector pair 3 times in
        series before giving up.

    timeout: number, optional
        The maximum time to allow for the alignment before aborting. The
        timeout is checked after each walk step.
    """
    num = len(detectors)

    # Listify most optional arguments
    starts = as_list(starts, num)
    first_steps = as_list(first_steps, num, float)
    gradients = as_list(gradients, num)
    detector_fields = as_list(detector_fields, num)
    motor_fields = as_list(motor_fields, num)
    tolerances = as_list(tolerances, num)
    system = as_list(system)
    averages = as_list(averages, num)

    # Debug counters
    mirror_walks = 0
    yag_cycles = 0

    # Set up end conditions
    n_steps = 0
    start_time = time.time()
    timeout_error = False
    finished = [False] * num
    while True:
        for i in range(num):
            ok = (yield from prep_img_motors(i, detectors, timeout=15))
            yag_cycles += 1

            # Be loud if the yags fail to move! Operator should know!
            if not ok:
                err = "Detector motion timed out!"
                logger.error(err)
                raise RuntimeError(err)

            # Only choose a start position for the first move if it was given
            if n_steps == 0 and starts[i] is not None:
                firstpos = starts[i]
            else:
                firstpos = None

            # Give higher-level a chance to suspend before measuring centroid
            yield from checkpoint()

            # Check if we're already done
            pos = (yield from measure_centroid(detectors[i],
                                               target_field=detector_fields[i],
                                               average=averages[i]))
            logger.debug("recieved %s from measure_centroid on %s", pos,
                         detectors[i])
            try:
                pos = pos[0]
            except IndexError:
                pass
            if abs(pos - goals[i]) < tolerances[i]:
                logger.debug("beam aligned on %s without move", detectors[i])
                finished[i] = True
                if all(finished):
                    logger.debug("beam aligned on all yags")
                    break
                continue
            else:
                # If any of the detectors were wrong, reset all finished flags
                logger.debug("reset alignment flags before move")
                finished = [False] * num

            # Modify goal to use overshoot
            if i == 0:
                goal = goals[i]
            else:
                goal = (goals[i] - pos) * (1 + overshoot) + pos

            # Core walk
            full_system = system
            full_system.remove(motors[i])
            full_system.remove(detectors[i])
            logger.debug("Start walk from %s to %s on %s using %s",
                         pos, goal, detectors[i].name, motors[i].name)
            pos = (yield from walk_to_pixel(detectors[i], motors[i], goal,
                                            firstpos, gradient=gradients[i],
                                            target_fields=[detector_fields[i],
                                                           motor_fields[i]],
                                            first_step=first_steps[i],
                                            tolerance=tolerances[i],
                                            system=full_system,
                                            average=averages[i], max_steps=5))
            logger.debug("Walk reached pos %s on %s", pos, detectors[i].name)
            mirror_walks += 1

            # Be loud if the walk fails to reach the pixel!
            if abs(pos - goal) > tolerances[i]:
                err = "walk_to_pixel failed to reach the goal"
                logger.error(err)
                raise RuntimeError(err)

            # After each walk, check the global timeout.
            if timeout is not None and time.time() - start_time > timeout:
                logger.warning("Iterwalk has timed out")
                timeout_error = True
                break

        if timeout_error:
            break

        if all(finished):
            break

        # After each set of walks, check if we've exceeded max_walks
        n_steps += 1
        if max_walks is not None and n_steps > max_walks:
            logger.info("Iterwalk has reached the max_walks limit")
            break
    logger.debug("Finished in %.2fs after %s mirror walks and %s yag cycles",
                 time.time() - start_time, mirror_walks, yag_cycles)
