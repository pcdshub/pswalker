#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import time
import logging
from pprint import pprint
from functools import partial
from collections import OrderedDict, ChainMap

###############
# Third Party #
###############
import numpy as np
from pcdsdevices.sim.pim import PIM
from pcdsdevices.sim.source import Undulator
from pcdsdevices.sim.mirror import OffsetMirror

##########
# Module #
##########
from .utils.pyUtils import isiterable

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

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
    logger.debug("Calculated one_bounce x position using: \na1={0}, x0={1}, \
xp0={2}, x1={3}, z1={4}, z2={5}. \nResult: {6}".format(
            a1, x0, xp0, x1, z1, z2, result))
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
    logger.debug("Calculated two_bounce x position using: \nalphas={0}, x0={1}, \
xp0={2}, x1={3}, z1={4}, x2={5}, z2={6}, z3={7}. \nResult: {8}".format(
            alphas, x0, xp0, x1, z1, x2, z2, z3, result))
    return result

def _x_to_pixel(x, pim):
    logger.debug("Converting x position to pixel on pim '{0}'.".format(pim.name))
    cam = pim.detector.cam
    result = np.round(np.floor(
        cam.size.size_x.value / 2) + (x - pim.sim_x.value) * \
                      cam.size.size_x.value / cam.resolution.resolution_x.value)
    logger.debug("Result: {0}".format(result))
    return result

def _calc_cent_x(source, pim):
    logger.debug("Calculating no bounce beam position on '{0}' pim.".format(
            pim.name))
    x = source.sim_x.value + source.sim_xp.value*pim.sim_z.value
    return _x_to_pixel(x, pim)

def _m1_calc_cent_x(source, mirror, pim):
    logger.debug("Calculating one bounce beam position on '{0}' pim. ".format(
            pim.name))        
    x = one_bounce(mirror.sim_alpha.value*1e-6,
                   source.sim_x.value,
                   source.sim_xp.value,
                   mirror.sim_x.value,
                   mirror.sim_z.value,
                   pim.sim_z.value)
    return _x_to_pixel(x, pim)

def _m1_m2_calc_cent_x(source, mirror_1, mirror_2, pim):
    logger.debug("Calculating two bounce beam position on '{0}' pim. ".format(
            pim.name))            
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


class TestBase(object):
    """
    When you want things to be Ophyd-like but are too lazy to make it real
    Opyhd
    """
    def nameify_keys(self, d):
        return {self.name + "_" + key : value
                for key, value in d.items()}

def patch_pims(pims, mirrors=OffsetMirror("TEST_MIRROR"), 
               source=Undulator("TEST_UND")):
    if not isiterable(mirrors):
        mirrors = [mirrors]
    #Change unit s 
    if not isiterable(pims):
        pims = [pims]
    logger.info("Patching {0} pim(s)".format(len(pims)))
    for pim in pims:
        if not mirrors or pim.sim_z.value <= mirrors[0].sim_z.value:
            logger.debug("Patching '{0}' with no bounce equation.".format(
                    pim.name))
            pim.detector._get_readback_centroid_x = partial(_calc_cent_x, source, pim)
        elif mirrors[0].sim_z.value < pim.sim_z.value:
            if len(mirrors) == 1:
                logger.debug("Patching '{0}' with one bounce equation.".format(
                        pim.name))
                pim.detector._get_readback_centroid_x = partial(_m1_calc_cent_x, source,
                                                                mirrors[0], pim)
            elif pim.sim_z.value <= mirrors[1].sim_z.value:
                logger.debug("Patching '{0}' with one bounce equation.".format(
                        pim.name))
                pim.detector._get_readback_centroid_x = partial(_m1_calc_cent_x, source,
                                                                mirrors[0], pim)
            elif mirrors[1].sim_z.value < pim.sim_z.value:
                logger.debug("Patching '{0}' with two bounce equation.".format(
                        pim.name))
                pim.detector._get_readback_centroid_x = partial(_m1_m2_calc_cent_x , source,
                                                                mirrors[0], mirrors[1], pim)
    if len(pims) == 1:
        return pims[0]
    return pims
