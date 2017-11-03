#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import logging
import uuid
from copy import copy

from bluesky.plan_stubs import checkpoint, mv, wait as plan_wait, abs_set

from .plans import walk_to_pixel, measure_average
from .plan_stubs import prep_img_motors
from .utils.argutils import as_list, field_prepend
from .utils.exceptions import FilterCountError

logger = logging.getLogger(__name__)


def iterwalk(detectors, motors, goals, starts=None, first_steps=1,
             gradients=None, detector_fields='centroid_x',
             motor_fields='alpha', tolerances=20, system=None, averages=1,
             overshoot=0, max_walks=None, timeout=None, recovery_plan=None,
             filters=None, tol_scaling=None):
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
        gauge the detector's response. This argument is ignored if
        ``gradients`` is provided.

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
        Other system parameters that we would like to read during the walk.

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

    recovery_plan: plan, optional
        A backup plan to run when no there is no readback on the detectors.
        This plan should expect a complete description of the situation in the
        form of all arguments given to iterwalk, except for recovery_plan. Note
        that these arguments are listified before being passed to
        recovery_plan. It will also be passed ``index``, which is the index in
        all of the list arguments that is currently active.
        Also note that there is no requirement to use all of the provided
        arguments. A good practice is to have recovery_plan accept and ignore
        kwargs while explicitly including desired keywords to use.

    filters: list of dictionaries
        Each entry in this list should be a valid input to the filters argument
        in the lower functions, such as walk_to_pixel and measure_average.
    
    tol_scaling: list of floats or Nones, optional
        Constants for adaptive tolerances. Nones or omitting this argument
        reverts to fixed tolerance. For early walks with a starting point far
        from the goal, tolerance for the walk is set at
        current_dist/tol_scaling instead of the set tolerance. Scaling ends
        when calculated tolerance < targeted tolerance.  
    """
    num = len(detectors)

    # Listify most optional arguments
    goals = as_list(goals, num)
    starts = as_list(starts, num)
    first_steps = as_list(first_steps, num, float)
    gradients = as_list(gradients, num)
    detector_fields = as_list(detector_fields, num)
    motor_fields = as_list(motor_fields, num)
    tolerances = as_list(tolerances, num)
    system = as_list(system)
    averages = as_list(averages, num)
    filters = as_list(filters, num)
    tol_scaling = as_list(tol_scaling, num)

    logger.debug("iterwalk aligning %s to %s on %s",
                 motors, goals, detectors)

    # Debug counters
    mirror_walks = 0
    yag_cycles = 0
    recoveries = 0
    # Set up end conditions
    n_steps = 0
    start_time = time.time()
    models   = [None]* num
    finished = [False] * num
    done_pos = [0] * num
    selected_tol = [None] * num

    moving_to_nominal = False
    group = str(uuid.uuid4())
    for mot in motors:
        try:
            position = mot.nominal_position
        except AttributeError:
            continue
        if position is not None:
            yield from abs_set(mot, mot.nominal_position, group=group)
            moving_to_nominal = True
    if moving_to_nominal:
        yield from plan_wait(group=group)

    while True:
        index = 0
        while index < num:
            try:
                # Before each walk, check the global timeout.
                if timeout is not None and time.time() - start_time > timeout:
                    raise RuntimeError("Iterwalk has timed out after %s s",
                                       time.time() - start_time)

                logger.debug("putting imager in")
                ok = (yield from prep_img_motors(index, detectors, timeout=15))
                yag_cycles += 1

                # Be loud if the yags fail to move! Operator should know!
                if not ok:
                    err = "Detector motion timed out!"
                    logger.error(err)
                    raise RuntimeError(err)

                # Choose a start position for the first move if it was given
                if n_steps == 0 and starts[index] is not None:
                    firstpos = starts[index]
                else:
                    firstpos = None

                # Give higher-level a chance to recover or suspend
                yield from checkpoint()

                # Set up the system to not include the redundant objects
                full_system = copy(system)
                try:
                    full_system.remove(motors[index])
                except ValueError:
                    pass
                try:
                    full_system.remove(detectors[index])
                except ValueError:
                    pass

                # Set flag for needing recovery before walking
                recover_pre_walk = True
                original_position = motors[index].position

                # Check if we're already done
                logger.debug("measure_average on det=%s, mot=%s, sys=%s",
                             detectors[index], motors[index], full_system)
                avgs = (yield from measure_average([detectors[index],
                                                    motors[index]]
                                                    + full_system,
                                                    num=averages[index],
                                                    filters=filters[index]))

                pos = avgs[field_prepend(detector_fields[index],
                                         detectors[index])]
                logger.debug("recieved %s from measure_average on %s", pos,
                             detectors[index])

                if abs(pos - goals[index]) < tolerances[index]:
                    logger.info("Beam was aligned on %s without a move",
                                 detectors[index].name)
                    finished[index] = True
                    done_pos[index] = pos
                    if all(finished):
                        logger.debug("beam aligned on all yags")
                        break
                    # Increment index before restarting loop
                    index += 1
                    continue
                else:
                    # If any of the detectors were wrong, reset finished flags
                    logger.debug("reset alignment flags before move")
                    finished = [False] * num

                # Modify goal to use overshoot
                if index == 0:
                    goal = goals[index]
                else:
                    goal = (goals[index] - pos) * (1 + overshoot) + pos

                # Calculate adaptive tolerance - otherwise use static tolerance
                if tol_scaling[index] != None:
                    selected_tol[index] = \
                        abs(pos-goals[index]) / tol_scaling[index]
                    if selected_tol[index] < tolerances[index]:
                        selected_tol[index] = tolerances[index]
                else:
                    selected_tol[index] = tolerances[index]
                
                # Clear flag for needing recovery before walking
                recover_pre_walk = False

                # Core walk
                logger.info(('Starting walk of {} pixels on {} using {}'
                             ''.format(abs(pos - goal), detectors[index].name,
                                       motors[index].name)))
                logger.debug(('Starting walk from {} to {} on {} using {}'
                              ''.format(pos, goal, detectors[index].name,
                                        motors[index].name)))
                
                logger.debug("selected tolerance: {}".format(
                    selected_tol[index]))

                pos, models[index] = (
                    yield from walk_to_pixel(
                        detectors[index],
                        motors[index],
                        goal,
                        filters=filters[index],
                        start=firstpos,
                        gradient=gradients[index],
                        target_fields=[
                            detector_fields[index],
                            motor_fields[index]],
                        first_step=first_steps[index],
                        tolerance=selected_tol[index],
                        system=full_system,
                        average=averages[index],
                        max_steps=10))

                if models[index]:
                    try:
                        gradients[index] = models[index].result.values['slope']
                        logger.debug("Found equation of ({}, {}) between " 
                                     "linear fit of {} to {}"
                                     "".format(gradients[index],
                                               models[index].result.values['intercept'],
                                               motors[index].name,
                                               detectors[index].name))
                    except Exception as e:
                        logger.warning(e)
                        logger.warning("Unable to find gradient of " 
                                       "linear fit of {} to {}"
                                       "".format(motors[index].name,
                                                 detectors[index].name))

                logger.debug("Walk reached pos %s on %s", pos,
                             detectors[index].name)
                mirror_walks += 1

                # Be loud if the walk fails to reach the pixel!
                if abs(pos - goal) > selected_tol[index]:
                    err = "walk_to_pixel failed to reach the goal"
                    logger.error(err)
                    raise RuntimeError(err)

                finished[index] = True
                done_pos[index] = pos

                # Increment index before restarting loop
                index += 1
            except FilterCountError as err:
                if recovery_plan is None:
                    logger.error("No recovery plan, not attempting to recover")
                    raise

                # If we had to recover before walk_to_pixel,
                # get a fallback position for if the recovery fails
                if recover_pre_walk:
                    try:
                        fallback_pos = motors[index].nominal_position
                    except AttributeError:
                        fallback_pos = None
                    # Explicitly check again in case nominal_position is None
                    if fallback_pos is None:
                        fallback_pos = motors[index].position
                else:
                    # If we are recovering after walk_to_pixel, don't bother
                    # with the recovery plan. Just move back and adjust
                    # parameters.
                    logger.info(("Bad state reached during walk_to_pixel. "
                                 "Undoing walk_to_pixel..."))
                    yield from mv(motors[index], original_position)

                    # Reset the finished flag
                    finished = [False] * num

                    # Cut our step parameters in half, because they were
                    # probably too big
                    logger.info("Lowering initial step parameters...")
                    if gradients[index] is not None:
                        gradients[index] = gradients[index] * 2
                    if first_steps[index] is not None:
                        first_steps[index] = first_steps[index] / -2
                    continue

                ok = yield from recovery_plan(detectors=detectors,
                                              motors=motors, goals=goals,
                                              starts=starts,
                                              first_steps=first_steps,
                                              gradients=gradients,
                                              detector_fields=detector_fields,
                                              motor_fields=motor_fields,
                                              tolerances=tolerances,
                                              system=system,
                                              averages=averages,
                                              overshoot=overshoot,
                                              max_walks=max_walks,
                                              timeout=timeout,
                                              filters=filters,
                                              index=index)

                # Reset the finished tag because we moved something
                finished = [False] * num
                recoveries += 1

                # If recovery failed, move to nominal and switch to next device
                if not ok:
                    logger.info(("Recover failed, using fallback pos and "
                                 "trying next device alignment."))
                    yield from mv(motors[index], fallback_pos)
                    index += 1
                # Try again
                continue

        if all(finished):
            break

        # After each set of walks, check if we've exceeded max_walks
        n_steps += 1
        if max_walks is not None and n_steps > max_walks:
            logger.info("Iterwalk has reached the max_walks limit")
            break
    txt = 'Finished in %.2fs after %s mirror walks, %s yag cycles, and %s '
    txt += 'recoveries.\n'
    txt += 'Aligned to %s\n'
    txt += 'Goals were %s\n'
    txt += 'Deltas are %s\n'
    txt += 'Mirror positions are %s'
    logger.info(txt,
                time.time() - start_time,
                mirror_walks,
                yag_cycles,
                recoveries,
                done_pos,
                goals,
                [d - g for g, d in zip(goals, done_pos)],
                [m.position for m in motors])
