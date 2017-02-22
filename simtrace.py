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

def run_sim(mx, my, energy, fee_slit_x, fee_slit_y, lhoms, x0, x0p, y0p, m1h_x, 
            m1h_z, m1h_a, p2h_x, p2h_z, m2h_x, m2h_z, m2h_a, p3h_x, p3h_z, 
            dg3_x, dg3_z):
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
    lhoms: number
        Length of the HOMS mirror in meters.
    fee_slit_x : number
        Physical gap at the fee slits in the x direction in meters.
    fee_slit_y : number
        Physical gap at the fee slits in the y direction in meters.
    x0: number
        Offset of undulator from nominal position in meters.
    x0p: number
        Offset of undulator pointing from nominal positon in rad.
    y0p: number
        Offset of unulator pointing in y from nominal position in rad.
    m1h_x: number
        Offset of m1h from nominal x position in meters.
    m1h_z: number
        Offset of m1h from nominal z position in meters.
    m1h_a: number
        Offset of m1h's pitch from nominal alpha position in meters.
    p2h_x: number
        Offset of p2h from nominal x position in meters.
    p2h_z: number
        Offset of p2h from nominal z position in meters.
    m2h_x: number
        Offset of m2h from nominal x position in meters.
    m2h_z: number
        Offset of m2h from nominal z position in meters.
    m2h_a: number
        Offset of m2h's pitch from nominal alpha position in meters.
    p3h_x: number
        Offset of p3h from nominal x position in meters.
    p3h_z: number
        Offset of p3h from nominal z position in meters.
    dg3_x: number
        Offset of dg3 from nominal x position in meters.
    dg3_z: number
        Offset of dg3 from nominal z position in meters.


    Returns
    p2h, p3h, dg3 : matlab.mlarray.double
        Returns three arrays of matlab doubles. The entries can be accessed
        with two indices e.g. p2h[0][0] is the first pixel at camera p2h.
        I do not know the orientation of these images, but they are all
        oriented the same way.
    """
    mx         = float(mx)
    my         = float(my)
    energy     = float(energy)
    fee_slit_x = float(fee_slit_x)
    fee_sliy_y = float(fee_slit_y)
    lhoms      = float(lhoms)
    x0         = float(x0)
    x0p        = float(x0p)
    y0p        = float(y0p)
    m1h_x      = float(m1h_x)
    m1h_z      = float(m1h_z)
    m1h_a      = float(m1h_a)
    p2h_x      = float(p2h_x)
    p2h_z      = float(p2h_z)
    m2h_x      = float(m2h_x)
    m2h_z      = float(m2h_z)
    m2h_a      = float(m2h_a)
    p3h_x      = float(p3h_x)
    p3h_z      = float(p3h_z)
    dg3_x      = float(dg3_x)
    dg3_z      = float(dg3_z)
    (p2h, p3h, dg3) = eng.SimTrace(mx, my, energy, fee_slit_x, fee_slit_y, lhoms,
                                   x0, x0p, y0p, m1h_x, m1h_z, m1h_a, p2h_x, 
                                   p2h_z, m2h_x, m2h_z, m2h_a, p3h_x, p3h_z,
                                   dg3_x, dg3_z,
                                   nargout=3)
    return p2h, p3h, dg3
