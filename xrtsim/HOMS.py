# -*- coding: utf-8 -*-
"""

__author__ = "Konstantin Klementiev", "Roman Chernikov"
__date__ = "2017-03-22"

Created with xrtQook












"""

import numpy as np
import sys
sys.path.append(r"/reg/neh/home/apra/.conda/envs/myenv/lib/python2.7/site-packages")
import xrt.backends.raycing.sources as rsources
import xrt.backends.raycing.screens as rscreens
import xrt.backends.raycing.materials as rmats
import xrt.backends.raycing.oes as roes
import xrt.backends.raycing.apertures as rapts
import xrt.backends.raycing.run as rrun
import xrt.backends.raycing as raycing
import xrt.plotter as xrtplot
import xrt.runner as xrtrun

crystalSi01 = rmats.CrystalSi(
    name=None)


def build_beamline(und_x, und_xp, und_y, und_yp, und_z, p1h_x, p1h_z,
                  m1h_x, m1h_alpha, m1h_z, p2h_x, p2h_z, m2h_x, m2h_alpha, 
                  m2h_z, p3h_x, p3h_z, dg3_x, dg3_z):
    HOMS = raycing.BeamLine()

    HOMS.Source = rsources.GeometricSource(
        bl=HOMS,
        name=None,
        center=[-und_x, und_z, und_y],
        dx=0.1,
        dz=0.1,
        dxprime=0.0000005,
        dzprime=0.0000005)

    HOMS.P1H = rscreens.Screen(
        bl=HOMS,
        name=None,
        center=[-p1h_x*1e3, p1h_z*1e3, 0])

    HOMS.M1H = roes.OE(
        bl=HOMS,
        name=None,
        center=[-m1h_x*1e3, m1h_z*1e3, 0],
        pitch=m1h_alpha,
        positionRoll=-np.pi/2)

    HOMS.P2H = rscreens.Screen(
        bl=HOMS,
        name=None,
        center=[-p2h_x*1e3, p2h_z*1e3, 0])

    HOMS.M2H = roes.OE(
        bl=HOMS,
        name=None,
        center=[-m2h_x*1e3, m2h_z*1e3, 0],
        pitch=-m2h_alpha,
        positionRoll=np.pi/2)

    HOMS.P3H = rscreens.Screen(
        bl=HOMS,
        name=None,
        center=[-p3h_x*1e3, p3h_z*1e3, 0])

    HOMS.DG3 = rscreens.Screen(
        bl=HOMS,
        name=None,
        center=[-dg3_x*1e3, dg3_z*1e3, 0])

    return HOMS


def run_process(HOMS):
    SourceBeam = HOMS.Source.shine()

    P1Hbeam = HOMS.P1H.expose(
        beam=SourceBeam)

    M1HBeam, oe01beamLocal01 = HOMS.M1H.reflect(
        beam=SourceBeam)

    P2Hbeam = HOMS.P2H.expose(
        beam=M1HBeam)

    M2HBeam, oe02beamLocal01 = HOMS.M2H.reflect(
        beam=M1HBeam)

    P3HBeam = HOMS.P3H.expose(
        beam=M2HBeam)

    DG3Beam = HOMS.DG3.expose(
        beam=M2HBeam)

    outDict = {
        'M1HBeam': M1HBeam,
        'oe01beamLocal01': oe01beamLocal01,
        'M2HBeam': M2HBeam,
        'oe02beamLocal01': oe02beamLocal01,
        'P3HBeam': P3HBeam,
        'DG3Beam': DG3Beam,
        'SourceBeam': SourceBeam,
        'P1Hbeam': P1Hbeam,
        'P2Hbeam': P2Hbeam}
    return outDict


rrun.run_process = run_process


def align_beamline(HOMS, energy):
    SourceBeam = rsources.Beam(nrays=2)
    SourceBeam.a[:] = 0
    SourceBeam.b[:] = 1
    SourceBeam.c[:] = 0
    SourceBeam.x[:] = 0
    SourceBeam.y[:] = 0
    SourceBeam.z[:] = 0
    SourceBeam.state[:] = 1
    SourceBeam.E[:] = energy

    tmpy = HOMS.P1H.center[1]
    newx = HOMS.P1H.center[0]
    newz = HOMS.P1H.center[2]
    HOMS.P1H.center = (newx, tmpy, newz)
    print("P1H.center:", HOMS.P1H.center)

    P1Hbeam = HOMS.P1H.expose(
        beam=SourceBeam)
    tmpy = HOMS.M1H.center[1]
    newx = HOMS.M1H.center[0]
    newz = HOMS.M1H.center[2]
    HOMS.M1H.center = (newx, tmpy, newz)
    print("M1H.center:", HOMS.M1H.center)

    M1HBeam, oe01beamLocal01 = HOMS.M1H.reflect(
        beam=SourceBeam)
    tmpy = HOMS.P2H.center[1]
    newx = HOMS.P2H.center[0]
    newz = HOMS.P2H.center[2]
    HOMS.P2H.center = (newx, tmpy, newz)
    print("P2H.center:", HOMS.P2H.center)

    P2Hbeam = HOMS.P2H.expose(
        beam=M1HBeam)
    tmpy = HOMS.M2H.center[1]
    newx = HOMS.M2H.center[0]
    newz = HOMS.M2H.center[2]
    HOMS.M2H.center = (newx, tmpy, newz)
    print("M2H.center:", HOMS.M2H.center)

    M2HBeam, oe02beamLocal01 = HOMS.M2H.reflect(
        beam=M1HBeam)
    tmpy = HOMS.P3H.center[1]
    newx = HOMS.P3H.center[0]
    newz = HOMS.P3H.center[2]
    HOMS.P3H.center = (newx, tmpy, newz)
    print("P3H.center:", HOMS.P3H.center)

    P3HBeam = HOMS.P3H.expose(
        beam=M2HBeam)
    tmpy = HOMS.DG3.center[1]
    newx = HOMS.DG3.center[0]
    newz = HOMS.DG3.center[2]
    HOMS.DG3.center = (newx, tmpy, newz)
    print("DG3.center:", HOMS.DG3.center)

    DG3Beam = HOMS.DG3.expose(
        beam=M2HBeam)


def define_plots(yag_sz, yag_res, p1h_x, p2h_x, p3h_x, dg3_x):
    plots = []
    P1H = xrtplot.XYCPlot(
        beam=r"P1Hbeam",
        xaxis=xrtplot.XYCAxis(
            label=r"x",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2],
            offset=-p1h_x),
        yaxis=xrtplot.XYCAxis(
            label=r"z",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2]),
        caxis=xrtplot.XYCAxis(
            label=r"energy",
            unit=r"eV"),
        ePos=0,
        title=r"P1H")
    plots.append(P1H)

    P2H = xrtplot.XYCPlot(
        beam=r"P2Hbeam",
        xaxis=xrtplot.XYCAxis(
            label=r"x",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2],
            offset=-p2h_x),
        yaxis=xrtplot.XYCAxis(
            label=r"z",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2]),
        caxis=xrtplot.XYCAxis(
            label=r"energy",
            unit=r"eV"),
        ePos=0,
        title=r"P2H",
        contourFmt=r"%.3f")
    plots.append(P2H)

    P3H = xrtplot.XYCPlot(
        beam=r"P3HBeam",
        xaxis=xrtplot.XYCAxis(
            label=r"x",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2],
            offset=-p3h_x),
        yaxis=xrtplot.XYCAxis(
            label=r"z",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2]),
        caxis=xrtplot.XYCAxis(
            label=r"energy",
            unit=r"eV"),
        ePos=0,
        title=r"P3H")
    plots.append(P3H)

    DG3 = xrtplot.XYCPlot(
        beam=r"DG3Beam",
        xaxis=xrtplot.XYCAxis(
            label=r"x",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2],
            offset=-dg3_x),
        yaxis=xrtplot.XYCAxis(
            label=r"z",
            unit=r"m",
            bins=yag_res,
            factor=0.001,
            limits=[-yag_sz/2, yag_sz/2]),
        caxis=xrtplot.XYCAxis(
            label=r"energy",
            unit=r"eV"),
        ePos=0,
        title=r"DG3")
    plots.append(DG3)
    return plots


def ray_trace(und_x, und_xp, und_y, und_yp, und_z, p1h_x, p1h_z, m1h_x, 
              m1h_alpha, m1h_z, p2h_x, p2h_z, m2h_x, m2h_alpha, m2h_z, p3h_x, 
              p3h_z, dg3_x, dg3_z, yag_sz, yag_res, ret_imgs=False):
    
    HOMS = build_beamline(und_x, und_xp, und_y, und_yp, und_z, p1h_x, p1h_z, 
                  m1h_x, m1h_alpha, m1h_z, p2h_x, p2h_z, m2h_x, m2h_alpha, 
                  m2h_z, p3h_x, p3h_z, dg3_x, dg3_z)
    E0 = list(HOMS.Source.energies)[0]
    align_beamline(HOMS, E0)
    plots = define_plots(yag_sz, yag_res, p1h_x, p2h_x, p3h_x, dg3_x)
    xrtrun.run_ray_tracing(
        plots=plots,
        backend=r"raycing",
        beamLine=HOMS)
    if ret_imgs:
        return [plot.total2D for plot in plots]

if __name__ == '__main__':
    ray_trace()
