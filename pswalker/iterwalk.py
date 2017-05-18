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
             motor_fields='alpha', tolerances=20, system=None, averages=None,
             overshoot=0, max_walks=None, timeout=None, sort="z"):
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

    # Set up end conditions
    n_steps = 0
    start_time = time.time()
    timeout_error = False
    finished = [False] * num
    while True:
        for i in range(num):
            # Give higher-level a chance to suspend before moving yags
            yield from checkpoint()
            ok = (yield from prep_img_motors(i, detectors, timeout=15))

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

            # Check if we're already done
            pos = (yield from measure_centroid(detectors[i],
                                               target_field=detector_fields[i],
                                               average=averages[i]))
            if abs(pos - goals[i]) < tolerances[i]:
                finished[i] = True
                if all(finished):
                    break
                continue
            else:
                # If any of the detectors were wrong, reset all finished flags
                finished = [False] * num

            # Modify goal to use overshoot
            goal = (goals[i] - pos) * (1 + overshoot[i]) + pos

            # Core walk
            yield from checkpoint()
            full_system = motors + system
            full_system.pop(motors[i])
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

            # Be loud if the walk fails to reach the pixel!
            if abs(pos - goals[i]) > tolerances[i]:
                err = "walk_to_pixel failed to reach the goal"
                logger.error(err)
                raise RuntimeError(err)

            # After each walk, check the global timeout.
            if timeout is not None and time.time() - start_time > timeout:
                logger.info("Iterwalk has timed out")
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
