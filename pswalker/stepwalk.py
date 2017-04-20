#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bluesky.plans import run_decorator
from .plan_stubs import prep_img_motors


def stepwalk(walk_motors, img_motors, img_dets, goals, moves, overshoot=5,
             tolerance=3, md=None):
    """
    Plan to iteratively improve the positions of walk_motors so that img_dets
    are returning the correct goal values. Reach each goal independently and
    revisit old goals until we've converged.

    Parameters
    ----------
    walk_motors: list of OphydObject
        Motors that we need to tweak to reach our goals. The set methods must
        accept floats. The ordering must correspond 1 to 1 with the desired
        detector to use.
    img_motors: list of OphydObject
        Motors that move the detectors in or out. These must implement a set
        method that accepts "IN" and "OUT" as arguments, reacting accordingly.
        This ordering must correspond 1 to 1 with the detectors they are
        attached to.
    img_dets: list of OphydObject
        Detectors to check our value. The read method must return a scalar that
        can be compared to the goal scalar.
    goals: list of scalar
        These are the values we're trying to reach in img_dets. The ordering
        must match.
    moves: list of functions
        These are functions that tell us how far to move each walk motor to
        reach our desired goal. We will pass the distance from the goal and
        expect a motor delta. The ordering must match everything else.
    overshoot: number
        How far to overshoot on each step in percent. Overshooting can help
        converge in fewer steps.
    tolerance: number
        stepwalk will end when the img_det readings are within tolerance of the
        goals.
    md: dict, optional
        metadata dictionary
    """
    _md = {}
    _md.update(md or {})

    @run_decorator(md=_md)
    def stepwalk_inner(*args):
        yield from stepwalk_raw(*args)

    return (yield from stepwalk_inner(walk_motors, img_motors, img_dets, goals,
                                      moves, overshoot, tolerance))


def stepwalk_raw(walk_motors, img_motors, img_dets, goals, moves, overshoot,
                 tolerance):
    n_walk = len(walk_motors)
    if any((len(x) != n_walk for x in (img_motors, img_dets, goals, moves))):
        raise ValueError("All inputs to stepwalk must be equal-length lists")

    for i in range(n_walk):
        yield from prep_img_motors(i, img_motors, prev_out=True, tail_in=True)
