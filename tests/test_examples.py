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
# from pswalker.examples import (YAG, OMMotor, OffsetMirror, Source, patch_yags,
#                                _calc_cent_x, _m1_calc_cent_x,
#                                _m1_m2_calc_cent_x)

from pswalker.examples import (OffsetMirror, PIM)

# OffsetMirror tests

def test_OffsetMirror_instantiates():
    assert(OffsetMirror("TEST"))

def test_OffsetMirror_motors_all_read():
    om = OffsetMirror("TEST")
    assert(isinstance(om.gan_x_p.read(), OrderedDict))
    assert(isinstance(om.gan_x_s.read(), OrderedDict))
    assert(isinstance(om.gan_y_p.read(), OrderedDict))
    assert(isinstance(om.gan_y_s.read(), OrderedDict))
    assert(isinstance(om.pitch.read(), OrderedDict))

def test_OffsetMirror_runs_ophyd_functions():
    om = OffsetMirror("TEST")
    assert(isinstance(om.read(), OrderedDict))
    assert(isinstance(om.describe(), OrderedDict))
    assert(isinstance(om.describe_configuration(), OrderedDict))
    assert(isinstance(om.read_configuration(), OrderedDict))

def test_OffsetMirror_yag_patch_properties():
    om = OffsetMirror("TEST", x=10, y=15, z=20, alpha=1)
    assert(om._x == 10)
    assert(om._y == 15)
    assert(om._z == 20)
    assert(om._alpha == 1)
    om.gan_x_p.move(75)
    om.gan_y_p.move(100)
    om.z = 125
    om.move(50)
    assert(om._x == 75)
    assert(om._y == 100)
    assert(om._z == 125)
    assert(om._alpha == 50)

# PIM Tests

def test_PIM_instantiates():
    assert(PIM("TEST"))

def test_PIM_runs_ophyd_functions():
    pim = PIM("TEST")
    assert(isinstance(pim.read(), OrderedDict))
    assert(isinstance(pim.describe(), OrderedDict))
    assert(isinstance(pim.describe_configuration(), OrderedDict))
    assert(isinstance(pim.read_configuration(), OrderedDict))
    
def test_PIM_has_centroid():
    pim = PIM("TEST")
    assert(isinstance(pim.detector.stats2.centroid.x.read(), dict))
    assert(isinstance(pim.detector.stats2.centroid.y.read(), dict))
    
def test_PIM_fake_sleep_move_time():
    pim = PIM("TEST")
    pim.move("OUT")
    pim.fake_sleep = 1
    t0 = time.time()
    status = pim.move("IN")
    t1 = time.time() - t0
    assert(np.isclose(t1, pim.fake_sleep + 0.1, rtol=0.1))
    assert(pim.position == "IN")
    assert(status.success)

def test_PIM_yag_patch_properties():
    pim = PIM("TEST", x=10, y_in=15, y_diode=20, y_out=25, z=20)
    status = pim.move("OUT")
    assert(pim._x == 10)
    assert(pim._y == 25)
    assert(pim._z == 20)
    assert(status.success)
    status = pim.move("DIODE")
    assert(pim._y == 20)
    assert(status.success)
    status = pim.move("IN")
    assert(pim._y == 15)
    assert(status.success)

# def test_YAG_Mirror_instantiates():
#     assert YAG('test yag', 0, 0)

# def test_patch_yags_with_no_bounce_func(simple_two_bounce_system):
#     s, m1, m2 = simple_two_bounce_system
#     yag_1 = [YAG('test_yag', 0, 3)]
#     yag_2 = [YAG('test_yag', 0, 5)]
#     yag_3 = [YAG('test_yag', 0, 7)]
    
#     yag_1 = patch_yags(yag_1)
#     assert yag_1._cent_x() == _calc_cent_x(s, yag_1)

#     yag_2 = patch_yags(yag_2, m1)
#     assert yag_2._cent_x() == _calc_cent_x(s, yag_2)

#     yag_3 = patch_yags(yag_3, [m1,m2])
#     assert yag_3._cent_x() == _calc_cent_x(s, yag_3)

# def test_patch_yags_with_one_bounce_func(simple_two_bounce_system):
#     s, m1, m2 = simple_two_bounce_system
#     yag_1 = [YAG('test_yag', 0, 13)]
#     yag_2 = [YAG('test_yag', 0, 15)]
    
#     yag_1 = patch_yags(yag_1, [m1,m2])
#     assert yag_1._cent_x() == _m1_calc_cent_x(s, m1, yag_1)
    
#     yag_2 = patch_yags(yag_2, m1)
#     assert yag_2._cent_x() == _m1_calc_cent_x(s, m1, yag_2)

# def test_patch_yags_with_two_bounce_func(simple_two_bounce_system):
#     s, m1, m2 = simple_two_bounce_system
#     yag_1 = [YAG('test_yag', 0, 25)]    
#     yag_1 = patch_yags(yag_1, [m1,m2])
#     assert yag_1._cent_x() == _m1_m2_calc_cent_x(s, m1, m2, yag_1)

# def test_mirror_set_and_read():
#     mot = Mirror('mirror', 0, 50, 0)
#     set_x = 100
#     set_z = 10
#     set_a = 5
#     mot.set(x=set_x, z=set_z, alpha=set_a)
#     assert mot.read()[mot.name + '_x']['value'] == set_x
#     assert mot.read()[mot.name + '_z']['value'] == set_z
#     assert mot.read()[mot.name + '_alpha']['value'] == set_a

# def test_yag_set_and_read(one_bounce_system):
#     s, mot, yag = one_bounce_system
#     set_x = 100
#     set_z = 10
#     yag.set(x=set_x, z=set_z)    
#     yag = patch_yags(yag, [mot])    
#     assert yag.read()[yag.name + '_x']['value'] == set_x
#     assert yag.read()[yag.name + '_z']['value'] == set_z
#     assert yag.read()[yag.name + '_centroid_x']['value'] == _m1_calc_cent_x(s, mot, yag)
    

