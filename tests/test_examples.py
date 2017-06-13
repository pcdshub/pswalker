############
# Standard #
############
import time
import subprocess
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

from pswalker.examples import (OMMotor, OffsetMirror, PluginBase, StatsPlugin,
                               CamBase, PulnixCam, DetectorBase, PulnixDetector,
                               PIMPulnixDetector, PIMMotor, PIM)

# OMMotor Tests

def test_OMMotor_instantiates():
    assert(OMMotor("TEST"))

def test_OMMotor_runs_ophyd_functions():
    ommotor = OMMotor("TEST")
    assert(isinstance(ommotor.read(), OrderedDict))
    assert(isinstance(ommotor.describe(), OrderedDict))
    assert(isinstance(ommotor.describe_configuration(), OrderedDict))
    assert(isinstance(ommotor.read_configuration(), OrderedDict))

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

def test_OMMotor_fake_sleep_move_time():
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

def test_OffsetMirror_move_method():
    om = OffsetMirror("TEST")
    om.move(10)
    assert(om.position == 10)
    assert(om.pitch.position == 10)
    
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

# PluginBase Tests

def test_PluginBase_instantiates():
    assert(PluginBase("TEST"))

def test_PluginBase_runs_ophyd_functions():
    plugin = PluginBase("TEST")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

# StatsPlugin Tests

def test_StatsPlugin_instantiates():
    assert(StatsPlugin("TEST"))

def test_StatsPlugin_runs_ophyd_functions():
    plugin = StatsPlugin("TEST")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

# CamBase Tests

def test_CamBase_instantiates():
    assert(CamBase("TEST"))

def test_CamBase_runs_ophyd_functions():
    cam = CamBase("TEST")
    assert(isinstance(cam.read(), OrderedDict))
    assert(isinstance(cam.describe(), OrderedDict))
    assert(isinstance(cam.describe_configuration(), OrderedDict))
    assert(isinstance(cam.read_configuration(), OrderedDict))

# PulnixCam Tests

def test_PulnixCam_instantiates():
    assert(PulnixCam("TEST"))

def test_PulnixCam_runs_ophyd_functions():
    pulnix = PulnixCam("TEST")
    assert(isinstance(pulnix.read(), OrderedDict))
    assert(isinstance(pulnix.describe(), OrderedDict))
    assert(isinstance(pulnix.describe_configuration(), OrderedDict))
    assert(isinstance(pulnix.read_configuration(), OrderedDict))

# DetectorBase Tests

def test_DetectorBase_instantiates():
    assert(DetectorBase("TEST"))

def test_DetectorBase_runs_ophyd_functions():
    det = DetectorBase("TEST")
    assert(isinstance(det.read(), OrderedDict))
    assert(isinstance(det.describe(), OrderedDict))
    assert(isinstance(det.describe_configuration(), OrderedDict))
    assert(isinstance(det.read_configuration(), OrderedDict))

# PulnixDetector Tests

def test_PulnixDetector_instantiates():
    assert(PulnixDetector("TEST"))

def test_PulnixDetector_runs_ophyd_functions():
    pulnix_det = PulnixDetector("TEST")
    assert(isinstance(pulnix_det.read(), OrderedDict))
    assert(isinstance(pulnix_det.describe(), OrderedDict))
    assert(isinstance(pulnix_det.describe_configuration(), OrderedDict))
    assert(isinstance(pulnix_det.read_configuration(), OrderedDict))

def test_PulnixDetector_cam_component_reads():
    pulnix_det = PulnixDetector("TEST")
    assert(isinstance(pulnix_det.cam.read(), OrderedDict))

# PIMPulnixDetector Tests

def test_PIMPulnixDetector_instantiates():
    assert(PIMPulnixDetector("TEST"))

def test_PIMPulnixDetector_runs_ophyd_functions():
    pim_pulnix_det = PIMPulnixDetector("TEST")
    assert(isinstance(pim_pulnix_det.read(), OrderedDict))
    assert(isinstance(pim_pulnix_det.describe(), OrderedDict))
    assert(isinstance(pim_pulnix_det.describe_configuration(), OrderedDict))
    assert(isinstance(pim_pulnix_det.read_configuration(), OrderedDict))

def test_PIMPulnixDetector_stats_plugin_reads():
    pim_pulnix_det = PIMPulnixDetector("TEST")
    assert(isinstance(pim_pulnix_det.stats2.read(), OrderedDict))

# PIMMotor Tests

def test_PIMMotor_instantiates():
    assert(PIMMotor("TEST"))

def test_PIMMotor_runs_ophyd_functions():
    pmotor = PIMMotor("TEST")
    assert(isinstance(pmotor.read(), OrderedDict))
    assert(isinstance(pmotor.describe(), OrderedDict))
    assert(isinstance(pmotor.describe_configuration(), OrderedDict))
    assert(isinstance(pmotor.read_configuration(), OrderedDict))

def test_PIMMotor_transitions_states_correctly():
    pmotor = PIMMotor("TEST")
    status = pmotor.move("OUT")
    assert(pmotor.position == "OUT")
    assert(status.success)
    status = pmotor.move("IN")
    assert(pmotor.position == "IN")
    assert(status.success)
    status = pmotor.move("DIODE")
    assert(pmotor.position == "DIODE")
    assert(status.success)

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
    

