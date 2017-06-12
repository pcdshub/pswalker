############
# Standard #
############
import time
import subprocess

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

from pswalker.examples import (OMMotor, OffsetMirror)

def test_OMMotor_instantiates():
    assert(OMMotor("TEST"))

def test_OMMotor_runs_ophyd_functions_correctly():
    ommotor = OMMotor("TEST")
    assert(ommotor.read())
    assert(ommotor.describe())
    assert(ommotor.describe_configuration())
    assert(ommotor.read_configuration())

def test_OMMotor_moves_properly():
    ommotor = OMMotor("TEST")
    status = ommotor.move(10)
    assert(ommotor.position == 10)
    assert(status.success)
    
def test_OMMotor_velocity_move_time():
    ommotor = OMMotor("TEST")
    diff = 1
    next_pos = ommotor.position + diff
    ommotor.velocity.put(0.5)    
    t0 = time.time()
    status = ommotor.move(next_pos)
    t1 = time.time() - t0
    assert(np.isclose(t1, diff/ommotor.velocity.value  + 0.1, rtol=0.1))
    assert(ommotor.position == next_pos)
    assert(status.success)

def test_OMMOTOR_fake_sleep_move_time():
    ommotor = OMMotor("TEST")
    diff = 1
    next_pos = ommotor.position + diff
    ommotor.velocity.put(0)    
    ommotor.fake_sleep = 1
    t0 = time.time()
    status = ommotor.move(next_pos)
    t1 = time.time() - t0
    assert(np.isclose(t1, ommotor.fake_sleep + 0.1, rtol=0.1))
    assert(ommotor.position == next_pos)
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
#     assert mot.read()['x']['value'] == set_x
#     assert mot.read()['z']['value'] == set_z
#     assert mot.read()['alpha']['value'] == set_a

# def test_yag_set_and_read(one_bounce_system):
#     s, mot, yag = one_bounce_system
#     set_x = 100
#     set_z = 10
#     yag.set(x=set_x, z=set_z)    
#     yag = patch_yags(yag, [mot])    
#     assert yag.read()['x']['value'] == set_x
#     assert yag.read()['z']['value'] == set_z
#     assert yag.read()['centroid_x']['value'] == _m1_calc_cent_x(s, mot, yag)
    

