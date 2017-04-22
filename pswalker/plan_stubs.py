#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid

from bluesky.plans import wait as plan_wait, abs_set


def prep_img_motors(n_mot, img_motors, prev_out=True, tail_in=True):
    """
    Plan to prepare image motors for taking data. Moves the correct imagers in
    and waits for them to be ready.

    Parameters
    ----------
    n_mot: int
        Index of the motor in img_motors that we need to take data with.
    img_motors: list of OphydObject
        OphydObjects to move in or out. These objects need to have .set methods
        that accept the strings "IN" and "OUT", reacting appropriately. These
        should be ordered by increasing distance to the source.
    prev_out: bool, optional
        If True, pull out imagers closer to the source than the one we need to
        use. Default True. (True if imager blocks beam)
    tail_in: bool, optional
        If True, put in imagers after this one, to be ready for later. If
        False, don't touch them. We won't wait for the tail motors to move in.
    """
    prev_img_mot = str(uuid.uuid4())
    for i, mot in enumerate(img_motors):
        if i < n_mot and prev_out:
            yield from abs_set(mot, "OUT", group=prev_img_mot)
        elif i == n_mot:
            yield from abs_set(mot, "IN", group=prev_img_mot)
        elif tail_in:
            yield from abs_set(mot, "IN")

    yield from plan_wait(group=prev_img_mot)
