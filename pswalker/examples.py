#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to hold functions and classes to use in simulating walks.
"""
############
# Standard #
############
import time
import logging
from pprint import pprint
from functools import partial
from collections.abc import Iterable
from collections import OrderedDict, ChainMap

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from .sim.pim import PIM
from .sim.source import Undulator
from .sim.mirror import OffsetMirror

logger = logging.getLogger(__name__)


class TestBase(object):
    """
    When you want things to be Ophyd-like but are too lazy to make it real
    Opyhd
    """
    def nameify_keys(self, d):
        return {self.name + "_" + key : value
                for key, value in d.items()}

def isiterable(obj):
    """
    Function that determines if an object is an iterable, not including 
    str.

    Parameters
    ----------
    obj : object
        Object to test if it is an iterable.

    Returns
    -------
    bool : bool
        True if the obj is an iterable, False if not.
    """
    if isinstance(obj, str):
        return False
    else:
        return isinstance(obj, Iterable)

def one_bounce(a1, x0, xp0, x1, z1, z2):
    """
    Calculates the x position of the beam after bouncing off one flat mirror.

    Parameters
    ----------
    a1 : float
        Pitch of first mirror in radians

    x0 : float
        x position of the source in meters

    xp0 : float
        Pitch of source in radians

    x1 : float
        x position of the first mirror in meters

    z1 : float
        z position of the first mirror in meters

    z2 : float
        z position of the imager    
    """
    result = -2*a1*z1 + 2*a1*z2 - z2*xp0 + 2*x1 - x0
    return result

def two_bounce(alphas, x0, xp0, x1, z1, x2, z2, z3):
    """
    Calculates the x position of the beam after bouncing off two flat mirrors.
    
    Parameters
    ----------
    alphas : tuple
        Tuple of the mirror pitches (a1, a2) in radians

    x0 : float
        x position of the source in meters

    xp0 : float
        Pitch of source in radians

    x1 : float
        x position of the first mirror in meters

    z1 : float
        z position of the first mirror in meters

    x2 : float
        x position of the second mirror in meters
    
    z2 : float
        z position of the second mirror in meters

    z3 : float
        z position of imager
    """
    result = 2*alphas[0]*z1 - 2*alphas[0]*z3 - 2*alphas[1]*z2 + \
        2*alphas[1]*z3 + z3*xp0 - 2*x1 + 2*x2 + x0
    return result

def _x_to_pixel(x, pim):
    """
    Convert the inputted x position to a pixel on the inputted pim.

    Parameters
    ----------
    x : float
        The x position to be converted

    pim : PIM
        The simulated PIM object to convert on

    Returns
    -------
    result : int
        Pixel the x position corresponds to on the inputted pim.
    """
    cam = pim.detector.cam
    result = np.round(np.floor(
        cam.size.size_x.value / 2) + (x - pim.sim_x.value) * \
                      cam.size.size_x.value / cam.resolution.resolution_x.value)
    return result

def _calc_cent_x(source, pim):
    """
    Calculates the position of the beam in pixels at the inputted pim assuming
    there were no reflections in between.

    Parameters
    ----------
    source : Undulator
        The object simulating the source of the beam

    pim : PIM
        The simulated PIM object to convert on

    Returns
    -------
    result : int
        Pixel of the centroid of the beam at the pim
    """
    x = source.sim_x.value + source.sim_xp.value*pim.sim_z.value
    result = _x_to_pixel(x, pim)
    return result

def _m1_calc_cent_x(source, mirror, pim):
    """
    Calculates the position of the beam in pixels at the inputted pim assuming
    there was one reflection at the inputted mirror

    Parameters
    ----------
    source : Undulator
        The object simulating the source of the beam

    mirror : OffsetMirror
        The simulated mirror to calculate the reflection with

    pim : PIM
        The simulated PIM object to convert on

    Returns
    -------
    result : int
        Pixel of the centroid of the beam at the pim
    """    
    x = one_bounce(mirror.sim_alpha.value*1e-6,
                   source.sim_x.value,
                   source.sim_xp.value,
                   mirror.sim_x.value,
                   mirror.sim_z.value,
                   pim.sim_z.value)
    result = _x_to_pixel(x, pim)
    return result

def _m1_m2_calc_cent_x(source, mirror_1, mirror_2, pim):
    """
    Calculates the position of the beam in pixels at the inputted pim assuming
    there were two reflections at the inputted mirrors

    Parameters
    ----------
    source : Undulator
        The object simulating the source of the beam

    mirror_1 : OffsetMirror
        The simulated mirror to calculate the first reflection with

    mirror_2 : OffsetMirror
        The simulated mirror to calculate the second reflection with

    pim : PIM
        The simulated PIM object to convert on

    Returns
    -------
    result : int
        Pixel of the centroid of the beam at the pim
    """    
    x = two_bounce((mirror_1.sim_alpha.value*1e-6,
                    mirror_2.sim_alpha.value*1e-6),
                   source.sim_x.value,
                   source.sim_xp.value,
                   mirror_1.sim_x.value,
                   mirror_1.sim_z.value,
                   mirror_2.sim_x.value,
                   mirror_2.sim_z.value,
                   pim.sim_z.value)
    return _x_to_pixel(x, pim)

def patch_pims(pims, mirrors=OffsetMirror("TEST_MIRROR", "TEST_XY",
                                          name="test_mirror"),
               source=Undulator("TEST_UND", name="test_und")):
    """
    Takes the inputted set of pims and mirrors and then the internal centroid
    calculating function for the pims to be one of the ray-tracing equations
    according to their position relative to the mirrors

    It does this by looping through each of the pims and comparing the stored z
    position against the z positions of the mirrors, and then pads the centroid
    readback accordingly.

    Parameters
    ----------
    pims : PIM or list
        PIMs to patch

    mirrors : OffsetMirror or list, optional
        Mirrors to calculate reflections off

    source : Undulator, optional
        Object to function as the source of the beam

    Returns
    -------
    pims : PIM or list
        The inputted pim objects but with their centroid readbacks patched with
        the ray tracing functions.
    """
    # Make sure the inputted mirrors and pims are iterables
    if not isiterable(mirrors):
        mirrors = [mirrors]
    if not isiterable(pims):
        pims = [pims]

    # Go through each pim
    for pim in pims:
        # If the pim is before the first mirror or there arent any mirrors
        if not mirrors or pim.sim_z.value <= mirrors[0].sim_z.value:
            logger.debug("Patching '{0}' with no bounce equation.".format(
                    pim.name))
            pim.detector._get_readback_centroid_x = partial(
                _calc_cent_x, source, pim)
            
        elif mirrors[0].sim_z.value < pim.sim_z.value:
            # If there is only one mirror and the pim is after it
            if len(mirrors) == 1:
                logger.debug("Patching '{0}' with one bounce equation.".format(
                        pim.name))
                pim.detector._get_readback_centroid_x = partial(
                    _m1_calc_cent_x, source, mirrors[0], pim)
                
            # If the pim is behind the second mirror
            elif pim.sim_z.value <= mirrors[1].sim_z.value:
                logger.debug("Patching '{0}' with one bounce equation.".format(
                        pim.name))
                pim.detector._get_readback_centroid_x = partial(
                    _m1_calc_cent_x, source, mirrors[0], pim)

            # If the pim is after the second mirror
            elif mirrors[1].sim_z.value < pim.sim_z.value:
                logger.debug("Patching '{0}' with two bounce equation.".format(
                        pim.name))
                pim.detector._get_readback_centroid_x = partial(
                    _m1_m2_calc_cent_x , source, mirrors[0], mirrors[1], pim)

        # Patch the y centroid to always be the center of the image
        pim.detector._get_readback_centroid_y = lambda : (
            int(pim.detector.cam.size.size_x.value / 2))
        
    # Return just the pim if there was only one of them
    if len(pims) == 1:
        return pims[0]
    
    return pims
