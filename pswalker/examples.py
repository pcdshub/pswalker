############
# Standard #
############
import logging
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

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

def one_bounce(a1, x0, xp0, x1, z1, z2):
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
    result = -2*a1*z1 + 2*a1*z2 - z2*xp0 + 2*x1 - x0
    logger.debug("Calculated one_bounce x position using: \na1={0}, x0={1}, \
xp0={2}, x1={3}, z1={4}, z2={5}. \nResult: {6}".format(
            a1, x0, xp0, x1, z1, z2, result))
    return result

def two_bounce(alphas, x0, xp0, x1, z1, x2, z2, z3):
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
    result = 2*alphas[0]*z1 - 2*alphas[0]*z3 - 2*alphas[1]*z2 + \
        2*alphas[1]*z3 + z3*xp0 - 2*x1 + 2*x2 + x0
    logger.debug("Calculated two_bounce x position using: \nalphas={0}, x0={1}, \
xp0={2}, x1={3}, z1={4}, x2={5}, z2={6}, z3={7}. \nResult: {8}".format(
            alphas, x0, xp0, x1, z1, x2, z2, z3, result))
    return result

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
        self.log_pref = "{0} (Source) - ".format(self.name)
        logger.info('Created new Source object. Name: {0}'.format(self.name))
        
    def read(self):
        logger.info("{0}Reading Attributes.".format(self.log_pref))
        result = dict(ChainMap(*[motor.read() for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result

    def set(self, **kwargs):
        logger.info("{0}Setting Attributes.".format(self.log_pref))
        logger.debug("{0}Setting: {1}".format(self.log_pref, kwargs))
        self._x = kwargs.get('x', self._x)
        self._xp = kwargs.get('xp', self._xp)        
        for motor in self.motors:
            motor_params = motor.read()
            for key in kwargs.keys():    
                if key in motor_params:
                    motor.set(kwargs[key])
        return Status(done=True, success=True)

    def describe(self, *args, **kwargs):
        logger.debug("{0}Describing object.".format(self.log_pref))        
        result = dict(ChainMap(*[motor.describe(*args, **kwargs)
                                 for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))        
        return result
    
    def describe_configuration(self, *args, **kwargs):
        logger.debug("{0}Describing configuration.".format(self.log_pref))
        result = dict(ChainMap(*[motor.describe_configuration(*args, **kwargs)
                                 for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))             
        return result
    
    def read_configuration(self, *args, **kwargs):
        logger.debug("{0}Reading configuration.".format(self.log_pref))
        result = dict(ChainMap(*[motor.read_configuration(*args, **kwargs)
                                 for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    def subscribe(self, *args, **kwargs):
        logger.debug("{0}Running subscribe (currently empty).".format(self.log_pref))
        pass

    def trigger(self, *args, **kwargs):
        logger.debug("{0}Running trigger.".format(self.log_pref))
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
        self.log_pref = "{0} (Mirror) - ".format(self.name)
        logger.info('Created new Mirror object. Name: {0}'.format(self.name))

    def read(self):
        logger.info("{0}Reading Attributes.".format(self.log_pref))
        read_dict = dict(ChainMap(*[motor.read() for motor in self.motors]))
        if (read_dict['x']['value'] != self._x or
            read_dict['z']['value'] != self._z or
            read_dict['alpha']['value'] != self._alpha):
            self._x = read_dict['x']['value']
            self._z = read_dict['z']['value']
            self._alpha = read_dict['alpha']['value']
            read_dict = self.read()
        logger.debug("{0}Result: {1}".format(self.log_pref, read_dict))
        return read_dict
        

    def set(self, cmd=None, **kwargs):
        logger.info("{0}Setting Attributes.".format(self.log_pref))
        logger.debug("{0}Setting: CMD:{1}, {2}".format(self.log_pref, cmd, kwargs))
        if cmd in ("IN", "OUT"):
            pass  # If these were removable we'd implement it here
        elif cmd is not None:
            # Here is where we move the pitch motor if a value is set
            self._alpha = cmd
            return self.alpha.set(cmd)
        self._x = kwargs.get('x', self._x)
        self._z = kwargs.get('z', self._z)
        self._alpha = kwargs.get('alpha', self._alpha)
        for motor in self.motors:
            motor_params = motor.read()            
            for key in kwargs.keys():
                if key in motor_params:
                    motor.set(kwargs[key])
        return Status(done=True, success=True)

    def describe(self, *args, **kwargs):
        logger.debug("{0}Describing object.".format(self.log_pref))
        result = dict(ChainMap(*[motor.describe(*args, **kwargs)
                                 for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    def describe_configuration(self, *args, **kwargs):
        logger.debug("{0}Describing configuration.".format(self.log_pref))
        result = dict(ChainMap(*[motor.describe_configuration(*args, **kwargs)
                                 for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))             
        return result
    
    def read_configuration(self, *args, **kwargs):
        logger.debug("{0}Reading configuration.".format(self.log_pref))
        result = dict(ChainMap(*[motor.read_configuration(*args, **kwargs)
                                 for motor in self.motors]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    @property
    def blocking(self):
        logger.debug("{0}Check for blockng.".format(self.log_pref))
        return False

    def subscribe(self, *args, **kwargs):
        logger.debug("{0}Subscribing (currently empty).".format(self.log_pref))
        pass

    def trigger(self, *args, **kwargs):
        logger.debug("{0}Running trigger (default status).".format(self.log_pref))
        return Status(done=True, success=True)

    @property
    def position(self):
        return self.alpha.position


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
        self.log_pref = "{0} (YAG) - ".format(self.name)
        logger.info('Created new YAG object. Name: {0}'.format(self.name))

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
        logger.info("{0}Reading Attributes.".format(self.log_pref))        
        result = dict(ChainMap(*[dev.read(*args, **kwargs)
                                 for dev in self.devices]))
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    def set(self, cmd=None, **kwargs):
        logger.info("{0}Setting Attributes.".format(self.log_pref))
        logger.debug("{0}Setting: CMD:{1}, {2}".format(self.log_pref, cmd, kwargs))
        if cmd == "OUT":
            self.y_state = "OUT"
        elif cmd == "IN":
            self.y_state = "IN"
        if cmd is not None:
            self.run_subs()
            return Status(done=True, success=True)
        self._x = kwargs.get('x', self._x)
        self._z = kwargs.get('z', self._z)
        for dev in self.devices:
            dev_params = dev.read()            
            for key in kwargs.keys():
                if key in dev_params:
                    dev.set(kwargs[key])
        return Status(done=True, success=True)
    
    def trigger(self, *args, **kwargs):
        logger.debug("{0}Getting trigger.".format(self.log_pref))
        result = self.reader.trigger(*args, **kwargs)
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result

    def describe(self, *args, **kwargs):
        logger.debug("{0}Describing reader.".format(self.log_pref))        
        result = self.reader.describe(*args, **kwargs)
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    def describe_configuration(self, *args, **kwargs):
        logger.debug("{0}Describing reader configuration.".format(self.log_pref))        
        result = self.reader.describe_configuration(*args, **kwargs)
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    def read_configuration(self, *args, **kwargs):
        logger.debug("{0}Reading reader configuration.".format(self.log_pref))        
        result = self.reader.read_configuration(*args, **kwargs)
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result
    
    @property
    def blocking(self):
        logger.debug("{0}Check for blockng.".format(self.log_pref))        
        result = self.y_state == "IN"
        logger.debug("{0}Result: {1}".format(self.log_pref, result))
        return result

    def subscribe(self, function):
        """
        Get subs to run on demand
        """
        logger.debug("{0}Subscribing to function.".format(self.log_pref))        
        self.reader.subscribe(function)
        self._subs.append(function)
        logger.debug("{0}Function: {1}".format(self.log_pref, function))

    def run_subs(self):
        logger.debug("{0}Running subscribed functions".format(self.log_pref))
        for sub in self._subs:
            sub()

    def __repr__(self):
        if self.name:
            return self.name
        else:
            super().__repr__()


def _x_to_pixel(x, yag):
    logger.debug("Converting x position to pixel on yag '{0}'.".format(yag.name))
    result = np.round(np.floor(yag.pix[0]/2) + \
                    (1 - 2*yag.invert)*(x - yag._x) * \
                    yag.pix[0]/yag.size[0])
    logger.debug("Result: {0}".format(result))
    return result

def _calc_cent_x(source, yag):
    logger.debug("Calculating no bounce beam position on '{0}' yag. ".format(
            yag.name))    
    x = source._x + source._xp*yag._z
    return _x_to_pixel(x, yag)

def _m1_calc_cent_x(source, mirror_1, yag):
    logger.debug("Calculating one bounce beam position on '{0}' yag. ".format(
            yag.name))        
    x = one_bounce(mirror_1._alpha,
                   source._x,
                   source._xp,
                   mirror_1._x,
                   mirror_1._z,
                   yag._z)
    return _x_to_pixel(x, yag)

def _m1_m2_calc_cent_x(source, mirror_1, mirror_2, yag):
    logger.debug("Calculating two bounce beam position on '{0}' yag. ".format(
            yag.name))            
    x = two_bounce((mirror_1._alpha, mirror_2._alpha),
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
    logger.info("Patching {0} yag(s)".format(len(yags)))            
    for yag in yags:
        if yag._z <= mirrors[0]._z:
            logger.debug("Patching '{0}' with no bounce equation.".format(
                    yag.name))
            yag._cent_x = lambda : _calc_cent_x(
                source, yag)
        elif mirrors[0]._z < yag._z:
            if len(mirrors) == 1:
                logger.debug("Patching '{0}' with one bounce equation.".format(
                        yag.name))
                yag._cent_x = lambda : _m1_calc_cent_x(
                    source, mirrors[0], yag)
            elif yag._z <= mirrors[1]._z:
                logger.debug("Patching '{0}' with one bounce equation.".format(
                        yag.name))
                yag._cent_x = lambda : _m1_calc_cent_x(
                    source, mirrors[0], yag)
            elif mirrors[1]._z < yag._z:
                logger.debug("Patching '{0}' with two bounce equation.".format(
                        yag.name))
                yag._cent_x = lambda : _m1_m2_calc_cent_x(
                    source, mirrors[0], mirrors[1], yag)
    if len(yags) == 1:
        return yags[0]
    return yags
            
if __name__ == "__main__":
    p1h = YAG("p1h", 0, 0)
    feem1 = Mirror("feem1", 0, 90.510, 0)
    p2h = YAG("p2h", 0.015000, 95.000)
    feem2 = Mirror("feem2", 0.0317324, 101.843, 0)
    p3h = YAG("p3h", 0.0317324, 103.6600)
    hx2_pim = YAG("hx2_pim", 0.0317324, 150.0000)
    um6_pim = YAG("um6_pim", 0.0317324, 200.0000)
    dg3_pim = YAG("dg3_pim", 0.0317324, 375.0000)


    yags = [p1h, p2h, hx2_pim, um6_pim, dg3_pim]
    p1h, p2h, hx2_pim, um6_pim, dg3_pim = patch_yags(yags, [feem1, feem2])

    # print(p3h.cent_x())
    
    feem1.set(alpha=0.0013644716418)

    # print(p3h.cent_x())
    
    feem2.set(alpha=0.0013674199723)
    
    # print(p3h.cent_x())

    
    pprint(p3h.read()['centroid_x']['value'])
    # import ipdb; ipdb.set_trace()
    pprint(dg3_pim.read()['centroid_x']['value'])
