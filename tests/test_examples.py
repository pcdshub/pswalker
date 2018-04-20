#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import time
from collections import OrderedDict
###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from pswalker.examples import (patch_pims, _calc_cent_x, _m1_calc_cent_x,
                               _m1_m2_calc_cent_x)
from pswalker.sim import (source, mirror, pim)


def test_patch_pims_with_no_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    pim_1 = [pim.PIM('test_pim', name='pim_1', z=3)]
    pim_2 = [pim.PIM('test_pim', name='pim_2', z=5)]
    pim_3 = [pim.PIM('test_pim', name='pim_3', z=7)]
    
    pim_1 = patch_pims(pim_1)
    assert pim_1.detector.stats2.centroid.x.value == _calc_cent_x(s, pim_1)

    pim_2 = patch_pims(pim_2, m1)
    assert pim_2.detector.stats2.centroid.x.value == _calc_cent_x(s, pim_2)

    pim_3 = patch_pims(pim_3, [m1,m2])
    assert pim_3.detector.stats2.centroid.x.value == _calc_cent_x(s, pim_3)

def test_patch_pims_with_one_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    pim_1 = [pim.PIM('test_pim', name='pim_1', z=13)]
    pim_2 = [pim.PIM('test_pim', name='pim_1', z=15)]
    
    pim_1 = patch_pims(pim_1, [m1,m2])
    assert pim_1.detector.stats2.centroid.x.value == _m1_calc_cent_x(s, m1, 
                                                                     pim_1)
    
    pim_2 = patch_pims(pim_2, m1)
    assert pim_2.detector.stats2.centroid.x.value == _m1_calc_cent_x(s, m1, 
                                                                     pim_2)

def test_patch_pims_with_two_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    pim_1 = [pim.PIM('test_pim', name='pim_1', z=25)]    
    pim_1 = patch_pims(pim_1, [m1,m2])
    assert pim_1.detector.stats2.centroid.x.value == _m1_m2_calc_cent_x(
        s, m1, m2, pim_1)

def test_pim_set_and_read(one_bounce_system):
    s, mot, pim = one_bounce_system
    set_x = 100
    set_z = 10
    pim.sim_x.put(set_x)
    pim.sim_z.put(set_z)
    pim = patch_pims(pim, [mot])    
    assert pim.sim_x.value == set_x
    assert pim.sim_z.value == set_z
    assert pim.detector.stats2.centroid.x.value == _m1_calc_cent_x(s, mot, pim)
    

