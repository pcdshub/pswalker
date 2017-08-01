#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os.path

from bluesky.plans import run_wrapper
from bluesky.callbacks import LiveTable

from pcdsdevices.epics.pim import PIMMotor

from pswalker.plans import walk_to_pixel, measure_average, measure_centroid  # NOQA
from pswalker.plan_stubs import recover_threshold, prep_img_motors
from pswalker.iterwalk import iterwalk  # NOQA
from pswalker.skywalker import (homs_RE, homs_system,  # NOQA
                                homs_skywalker as skywalker,
                                pitch_key, cent_x_key,
                                m1h_pitch, m2h_pitch, hx2_cent_x, dg3_cent_x,
                                make_homs_recover)
from pswalker.suspenders import PvAlarmSuspend  # NOQA
from pswalker.callbacks import PositionSaving

run_dir = '/reg/g/pcds/pyps/apps/skywalker'
if not os.path.exists(run_dir):
    run_dir = os.path.abspath('.')
logfile = os.path.join(run_dir, 'log.txt')

#strm = logging.StreamHandler()
logging.basicConfig(level=logging.DEBUG, filename=logfile,
                    format='%(asctime)s - %(levelname)s ' +
                           '- %(name)s - %(message)s')
#logging.addHandler(strm, level=logging.INFO)
RE = homs_RE()
RE.verbose = True # Enables internal RE logging

system = homs_system()
m1h = system['m1h']
m1h2 = system['m1h2']
m2h = system['m2h']
m2h2 = system['m2h2']
xrtm2 = system['xrtm2']
xrtm22 = system['xrtm22']
hx2 = system['hx2']
dg3 = system['dg3']
mfxdg1 = system['mfxdg1']

xcsdg3 = PIMMotor("XCS:DG3:PIM2")
xcssb2 = PIMMotor("XCS:SB2:PIM6")
