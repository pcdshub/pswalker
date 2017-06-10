##########
# Module #
##########
from pswalker.examples import (YAG, Mirror, Source, patch_yags,
                               _calc_cent_x, _m1_calc_cent_x,
                               _m1_m2_calc_cent_x)

def test_YAG_Mirror_instantiates():
    assert YAG('test yag', 0, 0)
    assert Mirror('test mirror', 0, 0, 0)

def test_patch_yags_with_no_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    yag_1 = [YAG('test_yag', 0, 3)]
    yag_2 = [YAG('test_yag', 0, 5)]
    yag_3 = [YAG('test_yag', 0, 7)]
    
    yag_1 = patch_yags(yag_1)
    assert yag_1._cent_x() == _calc_cent_x(s, yag_1)

    yag_2 = patch_yags(yag_2, m1)
    assert yag_2._cent_x() == _calc_cent_x(s, yag_2)

    yag_3 = patch_yags(yag_3, [m1,m2])
    assert yag_3._cent_x() == _calc_cent_x(s, yag_3)

def test_patch_yags_with_one_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    yag_1 = [YAG('test_yag', 0, 13)]
    yag_2 = [YAG('test_yag', 0, 15)]
    
    yag_1 = patch_yags(yag_1, [m1,m2])
    assert yag_1._cent_x() == _m1_calc_cent_x(s, m1, yag_1)
    
    yag_2 = patch_yags(yag_2, m1)
    assert yag_2._cent_x() == _m1_calc_cent_x(s, m1, yag_2)

def test_patch_yags_with_two_bounce_func(simple_two_bounce_system):
    s, m1, m2 = simple_two_bounce_system
    yag_1 = [YAG('test_yag', 0, 25)]
    
    yag_1 = patch_yags(yag_1, [m1,m2])
    assert yag_1._cent_x() == _m1_m2_calc_cent_x(s, m1, m2, yag_1)

def test_mirror_set_and_read():
    mot = Mirror('mirror', 0, 50, 0)
    set_x = 100
    set_z = 10
    set_a = 5
    mot.set(x=set_x, z=set_z, alpha=set_a)
    assert mot.read()[mot.name + '_x']['value'] == set_x
    assert mot.read()[mot.name + '_z']['value'] == set_z
    assert mot.read()[mot.name + '_alpha']['value'] == set_a

def test_yag_set_and_read(one_bounce_system):
    s, mot, yag = one_bounce_system
    set_x = 100
    set_z = 10
    yag.set(x=set_x, z=set_z)    
    yag = patch_yags(yag, [mot])    
    assert yag.read()[yag.name + '_x']['value'] == set_x
    assert yag.read()[yag.name + '_z']['value'] == set_z
    assert yag.read()[yag.name + '_centroid_x']['value'] == _m1_calc_cent_x(s, mot, yag)
    

