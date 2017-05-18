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
from .utils.pyUtils import isiterable
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
    def __init__(self, name='Source', x=0, xp=0, noise_x=0, noise_xp=0,
                 fake_sleep_x=0, fake_sleep_xp=0, **kwargs):
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
        return (self._x + (1 - 2*self.invert) * \
                (self.cent_x() - np.floor(self.pix[0]/2)) * \
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
            for dev in self.devices:
                if key in dev.read():
                    dev.set(kwargs[key])
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


def _x_to_pixel(x, yag):
    return np.round(np.floor(yag.pix[0]/2) + \
                    (1 - 2*yag.invert)*(x - yag._x) * \
                    yag.pix[0]/yag.size[0])         

def _calc_cent_x(source, yag):
    x = source._x + source._xp*yag._z
    return _x_to_pixel(x, yag)

def _m1_calc_cent_x(source, mirror_1, yag):
    x = OneBounce(mirror_1._alpha,
                  source._x,
                  source._xp,
                  mirror_1._x,
                  mirror_1._z,
                  yag._z)
    return _x_to_pixel(x, yag)

def _m1_m2_calc_cent_x(source, mirror_1, mirror_2, yag):
    x = TwoBounce((mirror_1._alpha, mirror_2._alpha),
                  source._x,
                  source._xp,
                  mirror_1._x,
                  mirror_1._z,
                  mirror_2._x,
                  mirror_2._z,
                  yag._z)
    return _x_to_pixel(x, yag)

def patch_yags(yags, mirrors=Mirror('Inf Mirror', 0, float('Inf'), 0),
               source=Source('Zero Source', 0, 0)):
    if not isiterable(mirrors):
        mirrors = [mirrors]
    if not isiterable(yags):
        yags = [yags]
    for yag in yags:
        if yag._z <= mirrors[0]._z:
            yag._cent_x = lambda : _calc_cent_x(source,
                                               yag)
        elif mirrors[0]._z < yag._z:
            if len(mirrors) == 1:
                yag._cent_x = lambda : _m1_calc_cent_x(source,
                                                       mirrors[0],
                                                       yag)
            elif yag._z <= mirrors[1]._z:
                yag._cent_x = lambda : _m1_calc_cent_x(source,
                                                       mirrors[0],
                                                       yag)
            elif mirrors[1]._z < yag._z:
                yag._cent_x = lambda : _m1_m2_calc_cent_x(source,
                                                          mirrors[0],
                                                          mirrors[1],
                                                          yag)
    if len(yags) == 1:
        return yags[0]
    return yags
            
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
