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
from pcdsdevices.sim import (source, mirror, pim)


def test_patch_pims_with_no_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    yag_1 = [YAG('test_yag', z=3)]
    yag_2 = [YAG('test_yag', z=5)]
    yag_3 = [YAG('test_yag', z=7)]
    
    yag_1 = patch_pims(yag_1)
    assert yag_1.detector.stats2.centroid.x.value == _calc_cent_x(s, yag_1)

    yag_2 = patch_pims(yag_2, m1)
    assert yag_2.detector.stats2.centroid.x.value == _calc_cent_x(s, yag_2)

    yag_3 = patch_pims(yag_3, [m1,m2])
    assert yag_3.detector.stats2.centroid.x.value == _calc_cent_x(s, yag_3)

def test_patch_pims_with_one_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    yag_1 = [YAG('test_yag', z=13)]
    yag_2 = [YAG('test_yag', z=15)]
    
    yag_1 = patch_pims(yag_1, [m1,m2])
    assert yag_1.detector.stats2.centroid.x.value == _m1_calc_cent_x(s, m1, 
                                                                        yag_1)
    
    yag_2 = patch_pims(yag_2, m1)
    assert yag_2.detector.stats2.centroid.x.value == _m1_calc_cent_x(s, m1, 
                                                                        yag_2)

def test_patch_pims_with_two_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    yag_1 = [YAG('test_yag', z=25)]    
    yag_1 = patch_pims(yag_1, [m1,m2])
    assert yag_1.detector.stats2.centroid.x.value == _m1_m2_calc_cent_x(
        s, m1, m2, yag_1)

def test_yag_set_and_read(one_bounce_system):
    s, mot, yag = one_bounce_system
    set_x = 100
    set_z = 10
    yag.sim_x.put(set_x)
    yag.sim_z.put(set_z)
    yag = patch_pims(yag, [mot])    
    assert yag.sim_x.value == set_x
    assert yag.sim_x.value == set_z
    assert yag.detector.stats.centroid.x.value == _m1_calc_cent_x(s, mot, yag)
    

