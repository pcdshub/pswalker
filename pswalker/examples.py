############
# Standard #
############
import time
import logging
from pprint import pprint
from functools import partial
from collections import OrderedDict, ChainMap

###############
# Third Party #
###############
import numpy as np
from ophyd.signal import Signal
from ophyd.status import Status
from ophyd import PositionerBase
from pcdsdevices.device import Device
from pcdsdevices.epics import (mirror, pim)
from pcdsdevices.epics.areadetector import (base, plugins)
from pcdsdevices.component import (FormattedComponent, Component)

##########
# Module #
##########
from .utils.pyUtils import isiterable

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
        
    def read(self):
        result = dict(ChainMap(*[motor.read() for motor in self.motors]))
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
        result = dict(ChainMap(*[motor.describe(*args, **kwargs)
                                 for motor in self.motors]))
        return result
    
    def describe_configuration(self, *args, **kwargs):
        result = dict(ChainMap(*[motor.describe_configuration(*args, **kwargs)
                                 for motor in self.motors]))
        return result
    
    def read_configuration(self, *args, **kwargs):
        result = dict(ChainMap(*[motor.read_configuration(*args, **kwargs)
                                 for motor in self.motors]))
        return result
    
    def subscribe(self, *args, **kwargs):
        pass

    def trigger(self, *args, **kwargs):
        return Status(done=True, success=True)

class Mirror(object):
    # Remove this when beginning to put together higher level tests in conftests
    pass

class OMMotor(mirror.OMMotor):
    # TODO: Write a proper docstring
    """
    Offset Mirror Motor object used in the offset mirror systems. Mostly taken
    from ophyd.epics_motor.
    """
    # position
    user_readback = Component(Signal, value=0)
    user_setpoint = Component(Signal, value=0)

    # configuration
    velocity = Component(Signal)

    # motor status
    motor_is_moving = Component(Signal, value=0)
    motor_done_move = Component(Signal, value=1)
    high_limit_switch = Component(Signal, value=10000)
    low_limit_switch = Component(Signal, value=-10000)

    # status
    interlock = Component(Signal)
    enabled = Component(Signal)

    motor_stop = Component(Signal)

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, velocity=0, fake_noise=0, fake_sleep=0, 
                 refresh=0.1, settle_time=0, **kwargs):
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name, 
                         parent=parent, settle_time=settle_time, **kwargs)
        self.velocity.put(velocity)
        self.fake_noise = fake_noise
        self.fake_sleep = fake_sleep
        self.refresh = refresh

    def move(self, position, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Position to move to

        Returns
        -------
        status : MoveStatus
        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        ValueError
            On invalid positions
        RuntimeError
            If motion fails other than timing out
        """
        self.user_setpoint.put(position)

        # Switch to moving state
        self.motor_is_moving.put(1)
        self.motor_done_move.put(0)

        # Add uniform noise
        pos = position + np.random.uniform(-1, 1)*self.fake_noise

        # Make sure refresh is set to something sensible if using velo or sleep
        if (self.velocity.value or self.fake_sleep) and not self.refresh:
            self.refresh = 0.1

        # If velo is set, incrementally set the readback according to the refresh
        if self.velocity.value:
            next_pos = self.user_readback.value
            while next_pos < pos:
                self.user_readback.put(next_pos) 
                time.sleep(self.refresh)
                next_pos += self.velocity.value*self.refresh

        # If fake sleep is set, incrementatlly sleep while setting the readback
        elif self.fake_sleep:
            wait = 0
            while wait < self.fake_sleep:
                time.sleep(self.refresh)
                wait += self.refresh
                self.user_readback.put(wait/self.fake_sleep * pos)
        status = self.user_readback.set(pos)

        # Switch to finished state and wait for status to update
        self.motor_is_moving.put(0)
        self.motor_done_move.put(1)
        time.sleep(0.1)

    
class TestBase(object):
    """
    When you want things to be Ophyd-like but are too lazy to make it real
    Opyhd
    """
    def nameify_keys(self, d):
        return {self.name + "_" + key : value
                for key, value in d.items()}
        return status


class OffsetMirror(mirror.OffsetMirror):
    # TODO: Add all parameters to doc string
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
    # Gantry Motors
    gan_x_p = FormattedComponent(OMMotor, "STEP:{self._mirror}:X:P")
    gan_x_s = FormattedComponent(OMMotor, "STEP:{self._mirror}:X:S")
    gan_y_p = FormattedComponent(OMMotor, "STEP:{self._mirror}:Y:P")
    gan_y_s = FormattedComponent(OMMotor, "STEP:{self._mirror}:Y:S")
    
    # Pitch Motor
    pitch = FormattedComponent(OMMotor, "{self._prefix}")

    # Placeholder signals for non-implemented components
    piezo = Component(Signal)    
    coupling = Component(Signal)
    motor_stop = Component(Signal)

    def __init__(self, prefix, *, name=None, read_attrs=None, parent=None, 
                 configuration_attrs=None, section="", x=0, y=0, z=0, alpha=0, 
                 velo_x=0, velo_y=0, velo_alpha=0, refresh_x=0, refresh_y=0, 
                 refresh_alpha=0, noise_x=0, noise_y=0, noise_alpha=0, 
                 fake_sleep_x=0, fake_sleep_y=0, fake_sleep_alpha=0, **kwargs):
        prefix = "MIRR:TST:{0}".format(prefix)
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)

        # Simulation Attributes
        # Fake noise to readback and moves
        self.gan_x_p.fake_noise = self.gan_x_s.fake_noise = noise_x
        self.gan_y_p.fake_noise = self.gan_y_s.fake_noise = noise_y
        self.pitch.fake_noise = noise_alpha
        
        # Fake sleep for every move
        self.gan_x_p.fake_sleep = self.gan_x_s.fake_sleep = fake_sleep_x
        self.gan_y_p.fake_sleep = self.gan_y_s.fake_sleep = fake_sleep_y
        self.pitch.fake_sleep = fake_sleep_alpha

        # Velocity for every move
        self.gan_x_p.velocity.value = self.gan_x_s.velocity.value = velo_x
        self.gan_y_p.velocity.value = self.gan_y_s.velocity.value = velo_y
        self.pitch.velocity.value = velo_alpha

        # Refresh rate for moves
        self.gan_x_p.refresh = self.gan_x_s.refresh = refresh_x
        self.gan_y_p.refresh = self.gan_y_s.refresh = refresh_y
        self.pitch.refresh = refresh_alpha
        
        # Set initial position values
        self.gan_x_p.user_setpoint.put(x)
        self.gan_x_p.user_readback.put(x)
        self.gan_x_s.user_setpoint.put(x)
        self.gan_x_s.user_readback.put(x)
        self.gan_y_p.user_setpoint.put(y)
        self.gan_y_p.user_readback.put(y)
        self.gan_y_s.user_setpoint.put(y)
        self.gan_y_s.user_readback.put(y)
        self.pitch.user_setpoint.put(alpha)
        self.pitch.user_readback.put(alpha)
        self.z = z

    # Coupling motor isnt implemented as an example so override its properties
    @property
    def decoupled(self):
        return False

    @property
    def fault(self):
        return False

    @property
    def gdif(self):
        return 0.0

    # Properties to simplify yag patching
    @property
    def _x(self):
        return self.gan_x_p.user_readback.value

    @property
    def _y(self):
        return self.gan_y_p.user_readback.value

    @property
    def _z(self):
        return self.z

    @property
    def _alpha(self):
        return self.pitch.user_readback.value


class PluginBase(base.ADBase):
    # Partially inherit PluginBase
    def __init__(self, *args, configuration_attrs=None, **kwargs):
        if configuration_attrs is None:
            configuration_attrs = self._default_configuration_attrs
        # Turn array callbacks on during staging.
        # Without this, no array data is sent to the plugins.
        super().__init__(*args, configuration_attrs=configuration_attrs,
                         **kwargs)
        # make sure it is the right type of plugin
        if (self._plugin_type is not None and
                not self.plugin_type.get().startswith(self._plugin_type)):
            raise TypeError('Trying to use {!r} class which is for {!r} '
                            'plugin type for a plugin that reports being '
                            'of type {!r} with base prefix '
                            '{!r}'.format(self.__class__.__name__,
                                          self._plugin_type,
                                          self.plugin_type.get(), self.prefix))

        self.stage_sigs['blocking_callbacks'] = 'Yes'
        if self.parent is not None and hasattr(self.parent, 'cam'):
            self.stage_sigs.update([('parent.cam.array_callbacks', 1),])

    _default_configuration_attrs = ('port_name', 'nd_array_port', 'enable',
                                    'blocking_callbacks', 'plugin_type',
                                    'asyn_pipeline_config',
                                    'configuration_names')

    _html_docs = ['pluginDoc.html']
    _plugin_type = None
    _suffix_re = None

    array_counter = Component(Signal, value=0)
    array_rate = Component(Signal, value=0)
    asyn_io = Component(Signal, value=0)
    nd_attributes_file = Component(Signal, value=0)
    pool_alloc_buffers = Component(Signal, value=0)
    pool_free_buffers = Component(Signal, value=0)
    pool_max_buffers = Component(Signal, value=0)
    pool_max_mem = Component(Signal, value=0)
    pool_used_buffers = Component(Signal, value=0)
    pool_used_mem = Component(Signal, value=0)
    port_name = Component(Signal, value=0)

    stage = plugins.PluginBase.stage
    source_plugin = plugins.PluginBase.source_plugin
    describe_configuration = plugins.PluginBase.describe_configuration
    _asyn_pipeline = plugins.PluginBase._asyn_pipeline
    _asyn_pipeline_configuration_names = \
      plugins.PluginBase._asyn_pipeline_configuration_names

class PIMPulnixDetector(pim.PIMPulnixDetector):
    pass


class YAG(TestBase):
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
        result = dict(ChainMap(*[dev.read(*args, **kwargs)
                                 for dev in self.devices]))
        return self.nameify_keys(result)
    
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
        result = self.reader.trigger(*args, **kwargs)
        return result

    def describe(self, *args, **kwargs):
        result = self.reader.describe(*args, **kwargs)
        return self.nameify_keys(result)
    
    def describe_configuration(self, *args, **kwargs):
        result = self.reader.describe_configuration(*args, **kwargs)
        return self.nameify_keys(result)
    
    def read_configuration(self, *args, **kwargs):
        result = self.reader.read_configuration(*args, **kwargs)
        return self.nameify_keys(result)
    
    @property
    def blocking(self):
        result = self.y_state == "IN"
        return result

    def subscribe(self, function):
        """
        Get subs to run on demand
        """
        self.reader.subscribe(function)
        self._subs.append(function)

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

def patch_yags(*args, **kwargs):
    pass

# def patch_yags(yags, mirrors=Mirror('Inf Mirror', 0, float('Inf'), 0),
#                source=Source('Zero Source', 0, 0)):
#     if not isiterable(mirrors):
#         mirrors = [mirrors]
#     if not isiterable(yags):
#         yags = [yags]
#     logger.info("Patching {0} yag(s)".format(len(yags)))            
#     for yag in yags:
#         if yag._z <= mirrors[0]._z:
#             logger.debug("Patching '{0}' with no bounce equation.".format(
#                     yag.name))
#             yag._cent_x = partial(_calc_cent_x, source, yag)
#         elif mirrors[0]._z < yag._z:
#             if len(mirrors) == 1:
#                 logger.debug("Patching '{0}' with one bounce equation.".format(
#                         yag.name))
#                 yag._cent_x = partial(_m1_calc_cent_x, source, mirrors[0], yag)
#             elif yag._z <= mirrors[1]._z:
#                 logger.debug("Patching '{0}' with one bounce equation.".format(
#                         yag.name))
#                 yag._cent_x = partial(_m1_calc_cent_x, source, mirrors[0], yag)
#             elif mirrors[1]._z < yag._z:
#                 logger.debug("Patching '{0}' with two bounce equation.".format(
#                         yag.name))
#                 yag._cent_x = partial(_m1_m2_calc_cent_x, source, mirrors[0],
#                                       mirrors[1], yag)
#     if len(yags) == 1:
#         return yags[0]
#     return yags
            
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
