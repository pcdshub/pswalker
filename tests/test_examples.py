##########
# Module #
##########
from pswalker.examples import (YAG, Mirror, Source, patch_yags,
                               _cal_cent_x, _m1_calc_cent_x,
                               _m1_m2_calc_cent_x)

def test_YAG_Mirror_instantiates():
    assert YAG('test yag', 0, 0)
    assert Mirror('test mirror', 0, 0, 0)

def test_patch_yags_with_no_bounce_func():
    s = Source('test_source', 0, 0)
    m1 = Mirror('test_mirror_1', 0, 10, 0)
    m2 = Mirror('test_mirror_2', 5, 20, 0)
    yag_1 = [YAG('test_yag', 0, 5)]
    yag_2 = [YAG('test_yag', 0, 5)]
    yag_3 = [YAG('test_yag', 0, 5)]
    
    yag_1 = patch_yags(yag_1)
    assert yag_1._cent_x == lambda : _cal_cent_x(

    yag_2 = patch_yags(yag_2, m1)
    assert yag_2._cent_x == _cal_cent_x

    yag_3 = patch_yags(yag_3, [m1,m2])
    assert yag_3._cent_x == _cal_cent_x
    
    

