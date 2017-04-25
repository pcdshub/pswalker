############
# Standard #
############
from collections import OrderedDict, ChainMap
from pprint import pprint
###############
# Third Party #
###############
import numpy as np
from bluesky.examples import Mover, Reader
from ophyd.status import Status

##########
# Module #
##########

def OneBounce(a1, x0, xp0, x1, z1, z2):
    """
    Calculates the x position of the beam after bouncing off one flat mirror.

    Parameters
    ----------
    a1 : float
    	Pitch of first mirror in radians

    x0 : float
    	x position of the source in meters

    xp0 : float
    	Pitch of source in radians

    x1 : float
    	x position of the first mirror in meters

    z1 : float
    	z position of the first mirror in meters

    z2 : float
    	z position of the imager    
    """
    return -2*a1*z1 + 2*a1*z2 - z2*xp0 + 2*x1 - x0

def TwoBounce(alphas, x0, xp0, x1, z1, x2, z2, z3):
    """
    Calculates the x position of the beam after bouncing off two flat mirrors.
    
    Parameters
    ----------
    alphas : tuple
    	Tuple of the mirror pitches (a1, a2) in radians

    x0 : float
    	x position of the source in meters

    xp0 : float
    	Pitch of source in radians

    x1 : float
    	x position of the first mirror in meters

    z1 : float
    	z position of the first mirror in meters

    x2 : float
    	x position of the second mirror in meters
    
    z2 : float
    	z position of the second mirror in meters

    z3 : float
    	z position of imager
    """
    return 2*alphas[0]*z1 - 2*alphas[0]*z3 - 2*alphas[1]*z2 + 2*alphas[1]*z3 + \
        z3*xp0 - 2*x1 + 2*x2 + x0

class OneMirrorOneYagSystem(object):
    """
    System of a source, mirror and an imager.

    Parameters
    ----------
    name_s : str, optional
    	Alias for Source

    name_m1 : str, optional
    	Alias for Mirror

    name_y1 : str, optional
    	Alias for Yag
    
    x0 : float, optional
        Initial x position of source

    xp0 : float, optional
        Initial pointing of source
    
    x1 : float, optional
        Initial x position of mirror

    d1 : float, optional
        Initial z position of mirror

    a1 : float, optional
        Initial pitch of mirror

    x2 : float, optional
        Initial x position of yag

    d2 : float, optional
        Initial z position of yag

    noise_x0 : float, optional
        Multiplicative noise factor added to source x-motor readback

    noise_xp0 : float, optional
        Multiplicative noise factor added to source xp-motor readback

    noise_x1 : float, optional
        Multiplicative noise factor added to mirror x-motor readback

    noise_z1 : float, optional
        Multiplicative noise factor added to mirror z-motor readback

    noise_a1 : float, optional
        Multiplicative noise factor added to mirror alpha-motor readback

    noise_x2 : float, optional
        Multiplicative noise factor added to yag x-motor readback

    noise_z2 : float, optional
        Multiplicative noise factor added to yag z-motor readback
    
    fake_sleep_x0 : float, optional
    	Amount of time to wait after moving source x-motor

    fake_sleep_xp0 : float, optional
    	Amount of time to wait after moving source xp-motor

    fake_sleep_x1 : float, optional
    	Amount of time to wait after moving mirror x-motor

    fake_sleep_z1 : float, optional
    	Amount of time to wait after moving mirror z-motor

    fake_sleep_a1 : float, optional
    	Amount of time to wait after moving mirror alpha-motor

    fake_sleep_x2 : float, optional
    	Amount of time to wait after moving yag x-motor

    fake_sleep_z2 : float, optional
    	Amount of time to wait after moving yag z-motor

    pix_y1 : tuple, optional
    	Dimensions of yag in pixels

    size_y1 : tuple, optional
    	Dimensions of yag in meters

    invert_y1 : bool, optional
    	Invert the resulting beam displacement from center of yag
    """
    def __init__(self, **kwargs):
        self._name_s = kwargs.get("name_s", "Source")
        self._name_m1 = kwargs.get("name_m1", "Mirror 1")
        self._name_y1 = kwargs.get("name_y1", "YAG 1")        
        self._x0 = kwargs.get("x0", 0)
        self._xp0 = kwargs.get("xp0", 0)
        self._x1 = kwargs.get("x1", 0)
        self._z1 = kwargs.get("z1", 90.510)
        self._a1 = kwargs.get("a1", 0.0014)
        self._x2 = kwargs.get("x2", 0.0317324)
        self._z2 = kwargs.get("z2", 101.843)
        self._noise_x0 = kwargs.get("noise_x0", 0)
        self._noise_xp0 = kwargs.get("noise_xp0", 0)
        self._noise_x1 = kwargs.get("noise_x1", 0)
        self._noise_z1 = kwargs.get("noise_z1", 0)
        self._noise_a1 = kwargs.get("noise_a1", 0)
        self._noise_x2 = kwargs.get("noise_x2", 0)
        self._noise_z2 = kwargs.get("noise_z2", 0)
        self._fake_sleep_x0 = kwargs.get("fake_sleep_x0", 0)
        self._fake_sleep_xp0 = kwargs.get("fake_sleep_xp0", 0)
        self._fake_sleep_x1 = kwargs.get("fake_sleep_x1", 0)
        self._fake_sleep_z1 = kwargs.get("fake_sleep_z1", 0)
        self._fake_sleep_a1 = kwargs.get("fake_sleep_a1", 0)
        self._fake_sleep_x2 = kwargs.get("fake_sleep_x2", 0)
        self._fake_sleep_z2 = kwargs.get("fake_sleep_z2", 0)
        self._pix_y1 = kwargs.get("pix_y1", (1392, 1040))
        self._size_y1 = kwargs.get("size_y1", (0.0076, 0.0062))
        self._invert_y1 = kwargs.get("invert_y1", False)

        self.source = Source(self._name_s, self._x0, self._xp0,
                             noise_x=self._noise_x0, noise_xp=self._noise_xp0,
                             fake_sleep_x=self._fake_sleep_x0,
                             fake_sleep_xp=self._fake_sleep_xp0)        
        self.mirror_1 = Mirror(self._name_m1, self._x1, self._z1, self._a1,
                               noise_x=self._noise_x1, noise_alpha=self._noise_a1,
                               fake_sleep_x=self._fake_sleep_x1,
                               fake_sleep_z=self._fake_sleep_z1,
                               fake_sleep_alpha=self._fake_sleep_a1)
        self.yag_1 = YAG(self._name_y1, self._x2, self._z2, self._noise_x2,
                         self._noise_z2, pix=self._pix_y1, size=self._size_y1,
                         fake_sleep_x=self._fake_sleep_x2,
                         fake_sleep_z=self._fake_sleep_z2)
        
        self.yag_1._cent_x = self._calc_cent_x

    def _calc_cent_x(self):
        x = OneBounce(self.mirror_1._alpha,
                      self.source._x,
                      self.source._xp,
                      self.mirror_1._x,
                      self.mirror_1._z,
                      self.yag_1._z)
        return np.round(np.floor(self.yag_1.pix[0]/2) + \
                        (1 - 2*self._invert_y1)*(x - self.yag_1._x) * \
                        self.yag_1.pix[0]/self.yag_1.size[0])

class TwoMirrorTwoYagSystem(object):
    """
    System of a source, mirror and an imager.

    Parameters
    ----------
    name_s : str, optional
    	Alias for Source

    name_m1 : str, optional
    	Alias for first mirror

    name_m2 : str, optional
    	Alias for second mirror
    
    name_y1 : str, optional
    	Alias for first yag
    
    name_y2 : str, optional
    	Alias for second yag
    
    x0 : float, optional
        Initial x position of source

    xp0 : float, optional
        Initial pointing of source
    
    x1 : float, optional
        Initial x position of first mirror

    d1 : float, optional
        Initial z position of first mirror

    a1 : float, optional
        Initial pitch of first mirror

    x2 : float, optional
        Initial x position of second mirror

    d2 : float, optional
        Initial z position of second mirror

    a2 : float, optional
        Initial pitch of second mirror
    
    x3 : float, optional
        Initial x position of first yag

    d3 : float, optional
        Initial z position of first yag

    x4 : float, optional
        Initial x position of second yag

    d4 : float, optional
        Initial z position of second yag
    
    noise_x0 : float, optional
        Multiplicative noise factor added to source x-motor readback

    noise_xp0 : float, optional
        Multiplicative noise factor added to source xp-motor readback

    noise_x1 : float, optional
        Multiplicative noise factor added to first mirror x-motor readback

    noise_z1 : float, optional
        Multiplicative noise factor added to first mirror z-motor readback

    noise_a1 : float, optional
        Multiplicative noise factor added to first mirror alpha-motor readback

    noise_x2 : float, optional
        Multiplicative noise factor added to second mirror x-motor readback

    noise_z2 : float, optional
        Multiplicative noise factor added to second mirror z-motor readback

    noise_a2 : float, optional
        Multiplicative noise factor added to second mirror alpha-motor readback
    
    noise_x3 : float, optional
        Multiplicative noise factor added to first yag x-motor readback

    noise_z3 : float, optional
        Multiplicative noise factor added to first yag z-motor readback
    
    noise_x4 : float, optional
        Multiplicative noise factor added to second yag x-motor readback

    noise_z4 : float, optional
        Multiplicative noise factor added to second yag z-motor readback
    
    fake_sleep_x0 : float, optional
    	Amount of time to wait after moving source x-motor

    fake_sleep_xp0 : float, optional
    	Amount of time to wait after moving source xp-motor

    fake_sleep_x1 : float, optional
    	Amount of time to wait after moving first mirror x-motor

    fake_sleep_z1 : float, optional
    	Amount of time to wait after moving first mirror z-motor

    fake_sleep_a1 : float, optional
    	Amount of time to wait after moving first mirror alpha-motor

    fake_sleep_x2 : float, optional
    	Amount of time to wait after moving second mirror x-motor

    fake_sleep_z2 : float, optional
    	Amount of time to wait after moving second mirror z-motor

    fake_sleep_a2 : float, optional
    	Amount of time to wait after moving second mirror alpha-motor
    
    fake_sleep_x3 : float, optional
    	Amount of time to wait after moving first yag x-motor

    fake_sleep_z3 : float, optional
    	Amount of time to wait after moving first yag z-motor

    fake_sleep_x4 : float, optional
    	Amount of time to wait after moving second yag x-motor

    fake_sleep_z4 : float, optional
    	Amount of time to wait after moving second yag z-motor
    
    pix_y1 : tuple, optional
    	Dimensions of first yag in pixels

    size_y1 : tuple, optional
    	Dimensions of first yag in meters

    invert_y1 : bool, optional
    	Invert the resulting beam displacement from center of first yag

    pix_y2 : tuple, optional
    	Dimensions of second yag in pixels

    size_y2 : tuple, optional
    	Dimensions of second yag in meters

    invert_y2 : bool, optional
    	Invert the resulting beam displacement from center of second yag    
    """
    def __init__(self, **kwargs):
        self._name_s = kwargs.get("name_s", "Source")
        self._name_m1 = kwargs.get("name_m1", "Mirror 1")
        self._name_m2 = kwargs.get("name_m2", "Mirror 2")
        self._name_y1 = kwargs.get("name_y1", "YAG 1")
        self._name_y2 = kwargs.get("name_y2", "YAG 2")                
        # Initial Positions
        self._x0 = kwargs.get("x0", 0)
        self._xp0 = kwargs.get("xp0", 0)
        self._x1 = kwargs.get("x1", 0)
        self._z1 = kwargs.get("z1", 90.510)
        self._a1 = kwargs.get("a1", 0.0014)
        self._x2 = kwargs.get("x2", 0.0317324)
        self._z2 = kwargs.get("z2", 101.843)
        self._a2 = kwargs.get("a2", 0.0014)
        self._x3 = kwargs.get("x3", 0.0317324)
        self._z3 = kwargs.get("z3", 103.660)
        self._x4 = kwargs.get("x4", 0.0317324)
        self._z4 = kwargs.get("z4", 375.000)
        # Noise for positions
        self._noise_x0 = kwargs.get("noise_x0", 0)
        self._noise_xp0 = kwargs.get("noise_xp0", 0)
        self._noise_x1 = kwargs.get("noise_x1", 0)
        self._noise_z1 = kwargs.get("noise_z1", 0)
        self._noise_a1 = kwargs.get("noise_a1", 0)
        self._noise_x2 = kwargs.get("noise_x2", 0)
        self._noise_z2 = kwargs.get("noise_z2", 0)
        self._noise_a2 = kwargs.get("noise_a2", 0)
        self._noise_x3 = kwargs.get("noise_x3", 0)
        self._noise_z3 = kwargs.get("noise_z3", 0)
        self._noise_x4 = kwargs.get("noise_x4", 0)
        self._noise_z4 = kwargs.get("noise_z4", 0)
        # Fake Sleep for motors
        self._fake_sleep_x0 = kwargs.get("fake_sleep_x0", 0)
        self._fake_sleep_xp0 = kwargs.get("fake_sleep_xp0", 0)
        self._fake_sleep_x1 = kwargs.get("fake_sleep_x1", 0)
        self._fake_sleep_z1 = kwargs.get("fake_sleep_z1", 0)
        self._fake_sleep_a1 = kwargs.get("fake_sleep_a1", 0)
        self._fake_sleep_x2 = kwargs.get("fake_sleep_x2", 0)
        self._fake_sleep_z2 = kwargs.get("fake_sleep_z2", 0)
        self._fake_sleep_a2 = kwargs.get("fake_sleep_a2", 0)
        self._fake_sleep_x3 = kwargs.get("fake_sleep_x3", 0)
        self._fake_sleep_z3 = kwargs.get("fake_sleep_z3", 0)
        self._fake_sleep_x4 = kwargs.get("fake_sleep_x4", 0)
        self._fake_sleep_z4 = kwargs.get("fake_sleep_z4", 0)
        # Other
        self._pix_y1 = kwargs.get("pix_y1", (1392, 1040))
        self._size_y1 = kwargs.get("size_y1", (0.0076, 0.0062))
        self._invert_y1 = kwargs.get("invert_y1", False)
        self._pix_y2 = kwargs.get("pix_y2", (1392, 1040))
        self._size_y2 = kwargs.get("size_y2", (0.0076, 0.0062))
        self._invert_y2 = kwargs.get("invert_y2", False)

        self.source = Source(self._name_s, self._x0, self._xp0,
                             noise_x=self._noise_x0, noise_xp=self._noise_xp0,
                             fake_sleep_x=self._fake_sleep_x0,
                             fake_sleep_xp=self._fake_sleep_xp0)        
        self.mirror_1 = Mirror(self._name_m1, self._x1, self._z1, self._a1,
                               noise_x=self._noise_x1,
                               noise_alpha=self._noise_a1,
                               fake_sleep_x=self._fake_sleep_x1,
                               fake_sleep_z=self._fake_sleep_z1,
                               fake_sleep_alpha=self._fake_sleep_a2)
        self.mirror_2 = Mirror(self._name_m2, self._x2, self._z2, self._a2,
                               noise_x=self._noise_x2,
                               noise_alpha=self._noise_a2,
                               fake_sleep_x=self._fake_sleep_x2,
                               fake_sleep_z=self._fake_sleep_z2,
                               fake_sleep_alpha=self._fake_sleep_a2)
        self.yag_1 = YAG(self._name_y1, self._x3, self._z3, self._noise_x3,
                         self._noise_z3, pix=self._pix_y1, size=self._size_y1,
                         fake_sleep_x=self._fake_sleep_x3,
                         fake_sleep_z=self._fake_sleep_z3)
        self.yag_2 = YAG(self._name_y2, self._x4, self._z4, self._noise_x4,
                         self._noise_z4, pix=self._pix_y2, size=self._size_y2,
                         fake_sleep_x=self._fake_sleep_x4,
                         fake_sleep_z=self._fake_sleep_z4)
        
        self.yag_1._cent_x = self._m1_calc_cent_x
        self.yag_2._cent_x = self._m2_calc_cent_x

    def _x_to_pixel(self, yag):
        return np.round(np.floor(yag_1.pix[0]/2) + \
                        (1 - 2*self._invert_y1)*(x - yag_1._x) * \
                        yag_1.pix[0]/yag_1.size[0])                

    def _m1_calc_cent_x(self):
        x = TwoBounce((self.mirror_1._alpha, self.mirror_2._alpha),
                      self.source._x,
                      self.source._xp,
                      self.mirror_1._x,
                      self.mirror_1._z,
                      self.mirror_2._x,
                      self.mirror_2._z,
                      self.yag_1._z)
        return self._x_to_pixel(self.yag_1)

    def _m2_calc_cent_x(self):
        x = TwoBounce((self.mirror_1._alpha, self.mirror_2._alpha),
                      self.source._x,
                      self.source._xp,
                      self.mirror_1._x,
                      self.mirror_1._z,
                      self.mirror_2._x,
                      self.mirror_2._z,
                      self.yag_2._z)
        return self._x_to_pixel(self.yag_2)

    def get_components(self):
        return self.source, self.mirror_1, self.mirror_2, self.yag_1, self.yag_2

class TwoMirrorNYagSystem(object):
    """
    System of a source, mirror and an imager.

    Parameters
    ----------
    yags : list
    	List of already initialized yag objects.
    
    name_s : str, optional
    	Alias for Source

    name_m1 : str, optional
    	Alias for first mirror

    name_m2 : str, optional
    	Alias for second mirror
    
    x0 : float, optional
        Initial x position of source

    xp0 : float, optional
        Initial pointing of source
    
    x1 : float, optional
        Initial x position of first mirror

    d1 : float, optional
        Initial z position of first mirror

    a1 : float, optional
        Initial pitch of first mirror

    x2 : float, optional
        Initial x position of second mirror

    d2 : float, optional
        Initial z position of second mirror

    a2 : float, optional
        Initial pitch of second mirror
    
    noise_x0 : float, optional
        Multiplicative noise factor added to source x-motor readback

    noise_xp0 : float, optional
        Multiplicative noise factor added to source xp-motor readback

    noise_x1 : float, optional
        Multiplicative noise factor added to first mirror x-motor readback

    noise_z1 : float, optional
        Multiplicative noise factor added to first mirror z-motor readback

    noise_a1 : float, optional
        Multiplicative noise factor added to first mirror alpha-motor readback

    noise_x2 : float, optional
        Multiplicative noise factor added to second mirror x-motor readback

    noise_z2 : float, optional
        Multiplicative noise factor added to second mirror z-motor readback

    noise_a2 : float, optional
        Multiplicative noise factor added to second mirror alpha-motor readback
    
    fake_sleep_x0 : float, optional
    	Amount of time to wait after moving source x-motor

    fake_sleep_xp0 : float, optional
    	Amount of time to wait after moving source xp-motor

    fake_sleep_x1 : float, optional
    	Amount of time to wait after moving first mirror x-motor

    fake_sleep_z1 : float, optional
    	Amount of time to wait after moving first mirror z-motor

    fake_sleep_a1 : float, optional
    	Amount of time to wait after moving first mirror alpha-motor

    fake_sleep_x2 : float, optional
    	Amount of time to wait after moving second mirror x-motor

    fake_sleep_z2 : float, optional
    	Amount of time to wait after moving second mirror z-motor

    fake_sleep_a2 : float, optional
    	Amount of time to wait after moving second mirror alpha-motor
    """
    def __init__(self, **kwargs):
        self.yags = kwargs.get("yags", None)
        self._name_s = kwargs.get("name_s", "Source")
        self._name_m1 = kwargs.get("name_m1", "Mirror 1")
        self._name_m2 = kwargs.get("name_m2", "Mirror 2")
        # Initial Positions
        self._x0 = kwargs.get("x0", 0)
        self._xp0 = kwargs.get("xp0", 0)
        self._x1 = kwargs.get("x1", 0)
        self._z1 = kwargs.get("z1", 90.510)
        self._a1 = kwargs.get("a1", 0.0014)
        self._x2 = kwargs.get("x2", 0.0317324)
        self._z2 = kwargs.get("z2", 101.843)
        self._a2 = kwargs.get("a2", 0.0014)
        # Noise for positions
        self._noise_x0 = kwargs.get("noise_x0", 0)
        self._noise_xp0 = kwargs.get("noise_xp0", 0)
        self._noise_x1 = kwargs.get("noise_x1", 0)
        self._noise_z1 = kwargs.get("noise_z1", 0)
        self._noise_a1 = kwargs.get("noise_a1", 0)
        self._noise_x2 = kwargs.get("noise_x2", 0)
        self._noise_z2 = kwargs.get("noise_z2", 0)
        self._noise_a2 = kwargs.get("noise_a2", 0)
        # Fake Sleep for motors
        self._fake_sleep_x0 = kwargs.get("fake_sleep_x0", 0)
        self._fake_sleep_xp0 = kwargs.get("fake_sleep_xp0", 0)
        self._fake_sleep_x1 = kwargs.get("fake_sleep_x1", 0)
        self._fake_sleep_z1 = kwargs.get("fake_sleep_z1", 0)
        self._fake_sleep_a1 = kwargs.get("fake_sleep_a1", 0)
        self._fake_sleep_x2 = kwargs.get("fake_sleep_x2", 0)
        self._fake_sleep_z2 = kwargs.get("fake_sleep_z2", 0)
        self._fake_sleep_a2 = kwargs.get("fake_sleep_a2", 0)

        self.source = Source(self._name_s, self._x0, self._xp0,
                             noise_x=self._noise_x0, noise_xp=self._noise_xp0,
                             fake_sleep_x=self._fake_sleep_x0,
                             fake_sleep_xp=self._fake_sleep_xp0)        
        self.mirror_1 = Mirror(self._name_m1, self._x1, self._z1, self._a1,
                               noise_x=self._noise_x1,
                               noise_alpha=self._noise_a1,
                               fake_sleep_x=self._fake_sleep_x1,
                               fake_sleep_z=self._fake_sleep_z1,
                               fake_sleep_alpha=self._fake_sleep_a2)
        self.mirror_2 = Mirror(self._name_m2, self._x2, self._z2, self._a2,
                               noise_x=self._noise_x2,
                               noise_alpha=self._noise_a2,
                               fake_sleep_x=self._fake_sleep_x2,
                               fake_sleep_z=self._fake_sleep_z2,
                               fake_sleep_alpha=self._fake_sleep_a2)
        if self.yags:
            self.yags = self.patch_yags(self.yags)

    def _x_to_pixel(self, x, yag):
        return np.round(np.floor(yag.pix[0]/2) + \
                        (1 - 2*yag.invert)*(x - yag._x) * \
                        yag.pix[0]/yag.size[0])         

    def _cal_cent_x(self, yag):
        x = self.source._x + self.source._xp*yag._z
        return self._x_to_pixel(x, yag)

    def _m1_calc_cent_x(self, yag):
        x = OneBounce(self.mirror_1.read()['alpha']['value'],
                      self.source._x,
                      self.source._xp,
                      self.mirror_1._x,
                      self.mirror_1._z,
                      yag._z)
        return self._x_to_pixel(x, yag)
            
    def _m1_m2_calc_cent_x(self, yag):
        x = TwoBounce((self.mirror_1._alpha, self.mirror_2._alpha),
                      self.source._x,
                      self.source._xp,
                      self.mirror_1._x,
                      self.mirror_1._z,
                      self.mirror_2._x,
                      self.mirror_2._z,
                      yag._z)
        return self._x_to_pixel(x, yag)

    def patch_yags(self, yags):
        for yag in yags:
            if yag._z <= self.mirror_1._z:
                yag._cent_x = lambda : self._cal_cent_x(yag)
            elif self.mirror_1._z < yag._z <= self.mirror_2._z:
                yag._cent_x = lambda : self._m1_calc_cent_x(yag)
            elif self.mirror_2._z < yag._z:
                yag._cent_x = lambda : self._m1_m2_calc_cent_x(yag)
        return yags

class Source(object):
    """
    Simulation of the photon source (simplified undulator).

    Parameters
    ----------
    name : str
        Alias of Source

    x : float
        Initial position of x-motor

    xp : float
        Initial position of xp-motor

    noise_x : float, optional
        Multiplicative noise factor added to x-motor readback

    noise_xp : float, optional
        Multiplicative noise factor added to xp-motor readback

    fake_sleep_x : float, optional
    	Amount of time to wait after moving x-motor

    fake_sleep_xp : float, optional
    	Amount of time to wait after moving xp-motor    
    """
    def __init__(self, name, x, xp, noise_x, noise_xp, fake_sleep_x=0,
                 fake_sleep_xp=0):
        self.name = name
        self.noise_x = noise_x
        self.noise_xp = noise_xp
        self.fake_sleep_x = fake_sleep_x
        self.fake_sleep_xp = fake_sleep_xp
        self.x = Mover('X Motor', OrderedDict(
                [('x', lambda x: x + np.random.uniform(-1, 1)
                  * self.noise_x),
                 ('x_setpoint', lambda x: x)]), {'x': x})
        self.xp = Mover('XP Motor', OrderedDict(
                [('xp', lambda xp: xp + np.random.uniform(-1, 1)
                  * self.noise_xp),
                 ('xp_setpoint', lambda xp: xp)]), {'xp': xp})
        self.motors = [self.x, self.xp]        
        self._x = x
        self._xp = xp
        
    def read(self):
        return dict(ChainMap(*[motor.read() for motor in self.motors]))

    def set(self, **kwargs):
        self._x = kwargs.get('x', self._x)
        self._xp = kwargs.get('xp', self._xp)        
        for key in kwargs.keys():
            for motor in self.motors:
                if key in motor.read():
                    motor.set(kwargs[key])
        return Status(done=True, success=True)


class Mirror(object):
    """
    Simulation of a simple flat mirror with assorted motors.
    
    Parameters
    ----------
    name : string
        Name of motor

    x : float
        Initial position of x-motor

    z : float
        Initial position of z-motor

    alpha : float
        Initial position of alpha-motor

    noise_x : float, optional
        Multiplicative noise factor added to x-motor readback

    noise_z : float, optional
        Multiplicative noise factor added to z-motor readback

    noise_alpha : float, optional
        Multiplicative noise factor added to alpha-motor readback
    
    fake_sleep_x : float, optional
    	Amount of time to wait after moving x-motor

    fake_sleep_z : float, optional
    	Amount of time to wait after moving z-motor

    fake_sleep_alpha : float, optional
    	Amount of time to wait after moving alpha-motor
    """
    def __init__(self, name, x, z, alpha, noise_x=0, noise_z=0,
                 noise_alpha=0, fake_sleep_x=0, fake_sleep_z=0,
                 fake_sleep_alpha=0):
        self.name = name
        self.noise_x = noise_x
        self.noise_z = noise_z
        self.noise_alpha = noise_alpha
        self.fake_sleep_x = fake_sleep_x
        self.fake_sleep_z = fake_sleep_z
        self.fake_sleep_alpha = fake_sleep_alpha
        self.x = Mover('X Motor', OrderedDict(
                [('x', lambda x: x + np.random.uniform(-1, 1)*self.noise_x),
                 ('x_setpoint', lambda x: x)]), {'x': x},
                       fake_sleep=self.fake_sleep_x)
        self.z = Mover('Z Motor', OrderedDict(
                [('z', lambda z: z + np.random.uniform(-1, 1)*self.noise_z),
                 ('z_setpoint', lambda z: z)]), {'z': z},
                       fake_sleep=self.fake_sleep_z)
        self.alpha = Mover('Alpha Motor', OrderedDict(
                [('alpha', lambda alpha: alpha +
                  np.random.uniform(-1, 1)*self.noise_alpha),
                 ('alpha_setpoint', lambda alpha: alpha)]), {'alpha': alpha},
                           fake_sleep=self.fake_sleep_alpha)
        self.motors = [self.x, self.z, self.alpha]
        self._x = x
        self._z = z
        self._alpha = alpha        

    def read(self):
        read_dict = dict(ChainMap(*[motor.read() for motor in self.motors]))
        if (read_dict['x']['value'] != self._x or
            read_dict['z']['value'] != self._z or
            read_dict['alpha']['value'] != self._alpha):
            self._x = read_dict['x']['value']
            self._z = read_dict['z']['value']
            self._alpha = read_dict['alpha']['value']
            return self.read()            
        return read_dict
        

    def set(self, cmd=None, **kwargs):
        if cmd in ("IN", "OUT"):
            pass  # If these were removable we'd implement it here
        elif cmd is not None:
            # Here is where we move the pitch motor if a value is set
            self._alpha = cmd
            return self.alpha.set(cmd)
        self._x = kwargs.get('x', self._x)
        self._z = kwargs.get('z', self._z)
        self._alpha = kwargs.get('alpha', self._alpha)
        for key in kwargs.keys():
            for motor in self.motors:
                if key in motor.read():
                    motor.set(kwargs[key])
        return Status(done=True, success=True)

    def describe(self, *args, **kwargs):
        return dict(ChainMap(*[motor.describe(*args, **kwargs)
                               for motor in self.motors]))

    def describe_configuration(self, *args, **kwargs):
        return dict(ChainMap(*[motor.describe_configuration(*args, **kwargs)
                               for motor in self.motors]))

    def read_configuration(self, *args, **kwargs):
        return dict(ChainMap(*[motor.read_configuration(*args, **kwargs)
                               for motor in self.motors]))
    
    @property
    def blocking(self):
        return False

    def subscribe(self, *args, **kwargs):
        pass

    def trigger(self, *args, **kwargs):
        return Status(done=True, success=True)


class YAG(object):
    """
    Simulation of a yag imager and the assorted motors.

    Parameters
    ----------
    name : str
        Alias of YAG

    x : float
        Initial position of x-motor

    z : float
        Initial position of z-motor

    noise_x : float, optional
        Multiplicative noise factor added to x-motor readback

    noise_z : float, optional
        Multiplicative noise factor added to z-motor readback

    fake_sleep_x : float, optional
    	Amount of time to wait after moving x-motor

    fake_sleep_z : float, optional
    	Amount of time to wait after moving z-motor

    pix : tuple, optional
    	Dimensions of imager in pixels

    size : tuple, optional
    	Dimensions of imager in meters
    """
    SUB_VALUE = "value"
    _default_sub = SUB_VALUE

    def __init__(self, name, x, z, noise_x=0, noise_z=0, fake_sleep_x=0,
                 fake_sleep_z=0, **kwargs):
        self.name = name
        self.noise_x = noise_x
        self.noise_z = noise_z
        self.fake_sleep_x = fake_sleep_x
        self.fake_sleep_z = fake_sleep_z
        self.x = Mover('X Motor', OrderedDict(
                [('x', lambda x: x + np.random.uniform(-1, 1)*self.noise_x),
                 ('x_setpoint', lambda x: x)]), {'x': x},
                       fake_sleep=self.fake_sleep_x)
        self.z = Mover('Z Motor', OrderedDict(
                [('z', lambda z: z + np.random.uniform(-1, 1)*self.noise_z),
                 ('z_setpoint', lambda z: z)]), {'z': z},
                       fake_sleep=self.fake_sleep_z)

        self.y_state = "OUT"
        self._subs = []
        self.pix = kwargs.get("pix", (1392, 1040))
        self.size = kwargs.get("size", (0.0076, 0.0062))
        self.invert = kwargs.get("invert", False)
        self.reader = Reader(self.name, {'centroid_x' : self.cent_x,
                                         'centroid_y' : self.cent_y,
                                         'centroid' : self.cent,
                                         'centroid_x_abs' : self.cent_x_abs})        
        self.devices = [self.x, self.z, self.reader]
        self._x = x
        self._z = z

    def _cent_x(self):
        return np.floor(self.pix[0]/2)

    def _cent_y(self):
        return np.floor(self.pix[1]/2)

    def cent_x(self):
        return self._cent_x()
    
    def cent_y(self):
        return self._cent_y()
    
    def cent(self):
        return (self.cent_x(), self.cent_y())

    def cent_x_abs(self):
        return (self._x + (1 - 2*self.invert)*(self.cent_x()-np.floor(self.pix[0]/2))* 
                self.size[0]/self.pix[0])
                                     
    def read(self, *args, **kwargs):
        return dict(ChainMap(*[dev.read(*args, **kwargs)
                               for dev in self.devices]))

    def set(self, cmd=None, **kwargs):
        if cmd == "OUT":
            self.y_state = "OUT"
        elif cmd == "IN":
            self.y_state = "IN"
        if cmd is not None:
            self.run_subs()
            return Status(done=True, success=True)
        self._x = kwargs.get('x', self._x)
        self._z = kwargs.get('z', self._z)
        for key in kwargs.keys():
            for motor in self.motors:
                if key in motor.read():
                    motor.set(kwargs[key])
        return Status(done=True, success=True)

    def trigger(self, *args, **kwargs):
        return self.reader.trigger(*args, **kwargs)    

    def describe(self, *args, **kwargs):
        return self.reader.describe(*args, **kwargs)

    def describe_configuration(self, *args, **kwargs):
        return self.reader.describe_configuration(*args, **kwargs)

    def read_configuration(self, *args, **kwargs):
        return self.reader.read_configuration(*args, **kwargs)
    
    @property
    def blocking(self):
        return self.y_state == "IN"

    def subscribe(self, function):
        """
        Get subs to run on demand
        """
        super().subscribe(function)
        self._subs.append(function)

    def run_subs(self):
        for sub in self._subs:
            sub()
                    
if __name__ == "__main__":
    sys = TwoMirrorSystem()
    m1 = sys.mirror_1
    m2 = sys.mirror_2
    y1 = sys.yag_1
    y2 = sys.yag_2
    # print("x: ", m.read()['x']['value'])
    # m.set(x=10)
    # print("x: ", m.read()['x']['value'])

    # import ipdb; ipdb.set_trace()
    # pprint(y1.read()['centroid_x']['value'])
    # pprint(y2.read()['centroid_x']['value'])

    m1.set(alpha=0.0013644716418)
    m2.set(alpha=0.0013674199723)
    
    pprint(y1.read()['centroid_x']['value'])
    pprint(y2.read()['centroid_x']['value'])    


    pprint(y1.describe_configuration())
