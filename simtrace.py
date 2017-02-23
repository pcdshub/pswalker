#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to call Jacek's simulation code from Python.
This relies on matlab's built in matlab.engine python interface that runs an
instance of matlab from a python session. This session does need a matlab
liscence to run.

For SLAC matlab liscences, you can check where they are available using:
/reg/common/package/scripts/matlic --show-users
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import matlab.engine

print("starting matlab engine...")
eng = matlab.engine.start_matlab()
print("matlab ready")

def run_sim(mx, my, energy, fee_slit_x, fee_slit_y,
            x0, x0p, x1, x1p, x2, x2p, lhoms, y0p):
    """
    Run Jacek's simulation code with beamline parameters to get simulated
    images at p2h, p3h, and dg3

    Parameters
    ----------
    mx : number
        Samples along the x-axis. Higher m means a longer calculation, but
        it will increase the accuracy.
    my : number
        Samples along the y-axis.
    energy : number
        X-ray energy in eV.
    fee_slit_x : number
        Physical gap at the fee slits in the x direction in meters.
    fee_slit_y : number
        Physical gap at the fee slits in the y direction in meters.
    x0: number
        Offset of undulator from nominal position in meters.
    x0p: number
        Offset of undulator pointing from nominal positon in rad.
    x1: number
        Offset of m1h from nominal position in meters.
    x1p: number
        Offset of m1h's pitch from nominal position in meters.
    x2: number
        Offset of m2h from nominal position in meters.
    x2p: number
        Offset of m2h's pitch from nominal position in meters.
    lhoms: number
        Length of the HOMS mirror in meters.
    y0p: number
        Offset of unulator pointing in y from nominal position in rad.

    Returns
    p2h, p3h, dg3 : matlab.mlarray.double
        Returns three arrays of matlab doubles. The entries can be accessed
        with two indices e.g. p2h[0][0] is the first pixel at camera p2h.
        I do not know the orientation of these images, but they are all
        oriented the same way.
    """
    mx = float(mx)
    my = float(my)
    energy = float(energy)
    fee_slit_x = float(fee_slit_x)
    fee_sliy_y = float(fee_slit_y)
    x0 = float(x0)
    x0p = float(x0p)
    x1 = float(x1)
    x1p = float(x1p)
    x2 = float(x2)
    x2p = float(x2p)
    lhoms = float(lhoms)
    y0p = float(y0p)
    (p2h, p3h, dg3) = eng.SimTrace(mx, my, energy, fee_slit_x, fee_slit_y,
                                   x0, x0p, x1, x1p, x2, x2p, lhoms, y0p,
                                   nargout=3)
    return p2h, p3h, dg3
