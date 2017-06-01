#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from bluesky.plans import run_wrapper
from bluesky.callbacks import LiveTable

from pcdsdevices.epics.pim import PIMMotor

from pswalker.plans import walk_to_pixel, measure_average, measure_centroid  # NOQA
from pswalker.plan_stubs import recover_threshold, prep_img_motors
from pswalker.iterwalk import iterwalk  # NOQA
from pswalker.skywalker import (homs_RE, homs_system,  # NOQA
                        homs_skywalker as skywalker,
                        run_homs_skywalker as run_skywalker)
from pswalker.suspenders import PvAlarmSuspend  # NOQA

re_logger = logging.getLogger("RunEngine")

RE = homs_RE()
RE.msg_hook = re_logger.debug

system = homs_system()
m1h = system['m1h']
m2h = system['m2h']
xrtm2 = system['xrtm2']
hx2 = system['hx2']
dg3 = system['dg3']

m1h.low_limit = -0.08
m1h.high_limit = 0.13
m2h.low_limit = -0.15
m2h.high_limit = 0.09

m1h_pitch = "MIRR:FEE1:M1H_pitch"
m2h_pitch = "MIRR:FEE1:M2H_pitch"
hx2_cent_x = "HX2:SB1:PIM_detector_stats2_centroid_y"
dg3_cent_x = "HFX:DG3:PIM_detector_stats2_centroid_y"

xcsdg3 = PIMMotor("XCS:DG3:PIM2")
xcssb2 = PIMMotor("XCS:SB2:PIM6")
