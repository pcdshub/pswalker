"""
Device configurations for Skywalker alignment
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
from pcdsdevices.epics.pim import PIM
from pcdsdevices.epics.mirror import OffsetMirror


##########
# Module #
##########

logger = logging.getLogger(__name__)

m1h = "MIRR:FEE1:M1H"
m1h_xy = "STEP:M1H"
m1h_name = "m1h"
m2h = "MIRR:FEE1:M2H"
m2h_xy = "STEP:M2H"
m2h_name = "m2h"
m3h = "MIRR:XRT:M2H"
m3h_xy = "XRT:M2H"
m3h_name = "xrtm2"
hx2 = "HX2:SB1:PIM"
hx2_name = "hx2"
dg3 = "HFX:DG3:PIM"
dg3_name = "dg3"
mfxdg1 = "MFX:DG1:PIM"
mfxdg1_det = "MFX:DG1:P6740"
mfxdg1_name = "mfxdg1"
mecy1 = "MEC:PIM1"
mecy1_det = "MEC:HXM:CVV:01"
mecy1_name = "mecy1"
pitch_key = "pitch"
cent_x_key = "detector_stats2_centroid_y"
fmt = "{}_{}"
m1h_pitch = fmt.format(m1h_name, pitch_key)
m2h_pitch = fmt.format(m2h_name, pitch_key)
hx2_cent_x = fmt.format(hx2_name, cent_x_key)
dg3_cent_x = fmt.format(dg3_name, cent_x_key)


def homs_system():
    """
    Instantiate the real mirror and yag objects from the real homs system, and
    pack them into a dictionary.

    Returns
    -------
    system: dict
    """
    system = {}
    system['m1h'] = OffsetMirror(m1h, m1h_xy, name=m1h_name)
    system['m1h2'] = OffsetMirror(m1h, m1h_xy, name=m1h_name+"2")
    system['m2h'] = OffsetMirror(m2h, m2h_xy, name=m2h_name)
    system['m2h2'] = OffsetMirror(m2h, m2h_xy, name=m2h_name+"2")
    system['xrtm2'] = OffsetMirror(m3h, m3h_xy, name=m3h_name)
    system['xrtm22'] = OffsetMirror(m3h, m3h_xy, name=m3h_name+"2")
    system['hx2'] = PIM(hx2, name=hx2_name)
    system['dg3'] = PIM(dg3, name=dg3_name)
    system['mfxdg1'] = PIM(mfxdg1, prefix_det=mfxdg1_det, name=mfxdg1_name)
    system['mecy1'] = PIM(mecy1, prefix_det=mecy1_det, name=mecy1_name)
    system['y1'] = system['hx2']
    system['y2'] = system['dg3']
    return system




