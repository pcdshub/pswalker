from ophyd.device import Device, Component, FormattedComponent
from ophyd.positioner import SoftPositioner

from .sim import SimDevice
from .signal import (Signal, FakeSignal)


class OMMotor(Device, SoftPositioner):
    """
    Simulated base class for each motor in the LCLS offset mirror system.

    Components
    ----------
    user_readback : FakeSignal
        Readback for current motor position

    user_setpoint : FakeSignal
        Setpoint signal for motor position

    velocity : FakeSignal
        Velocity signal for the motor

    motor_is_moving : FakeSignal
        Readback for bit that indicates if the motor is currenly moving

    motor_done_move : FakeSignal
        Readback for bit that indicates the motor has completed the desired
        motion

    high_limit_switch : FakeSignal
        Readback for high limit switch bit

    low_limit_switch : FakeSignal
        Readback for low limit switch bit

    interlock : FakeSignal
        Readback indicating if safe torque off (STO) is enabled

    enabled : FakeSignal
        Readback for stepper motor enabled bit

    motor_egu : FakeSignal
        Readback for units

    motor_stop : FakeSignal
        Not implemented in the PLC/EPICS but included as an empty signal to
        appease the Bluesky interface

    Parameters
    ---------- 
    prefix : str
        Prefix of the motor

    read_attrs : sequence of attribute names, optional
        The signals to be read during data acquisition (i.e., in read() and
        describe() calls)

    configuration_attrs : sequence of attribute names, optional
        The signals to be returned when asked for the motor configuration (i.e.
        in read_configuration(), and describe_configuration() calls)

    name : str, optional
        The name of the motor

    parent : instance or None, optional
        The instance of the parent device, if applicable

    settle_time : float, optional
        The amount of time to wait after moves to report status completion

    tolerance : float, optional
        Tolerance used to judge if the motor has reached its final position

    """
    # Simulated components
    # position
    user_readback = Component(FakeSignal, value=0)
    user_setpoint = Component(FakeSignal, value=0)

    # limits
    upper_ctrl_limit = Component(FakeSignal, value=0)
    lower_ctrl_limit = Component(FakeSignal, value=0)

    # configuration
    velocity = Component(Signal)

    # motor status
    motor_is_moving = Component(FakeSignal, value=0)
    motor_done_move = Component(FakeSignal, value=1)
    high_limit_switch = Component(FakeSignal, value=10000)
    low_limit_switch = Component(FakeSignal, value=-10000)

    # status
    interlock = Component(FakeSignal)
    enabled = Component(FakeSignal)

    # misc
    motor_egu = Component(FakeSignal, value='urad')

    # appease bluesky since there is no stop pv for these motors
    motor_stop = Component(FakeSignal)

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None, 
                 name=None, parent=None, velocity=0, noise=0, settle_time=0, 
                 noise_func=None, noise_type="uni", noise_args=(), 
                 noise_kwargs={}, timeout=None, **kwargs):
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name, 
                         parent=parent, timeout=timeout, **kwargs)
        self.velocity.put(velocity)
        self.noise = noise
        self.settle_time = settle_time
        self.noise_type = noise_type
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs
        self.user_setpoint.velocity = lambda : self.velocity.value
        
        # Set the readback val to always be the setpoint val
        self.user_readback._get_readback = lambda : self.user_setpoint.value

    def move(self, position, wait=False, **kwargs):
        status = super().move(position, wait=wait, **kwargs)
        # It takes one second for the status object to object update so set it
        # manually.
        status.success = True
        return status

    @property
    def noise(self):
        return self.user_readback.noise

    @noise.setter
    def noise(self, val):
        self.user_readback.noise = bool(val)

    @property
    def settle_time(self):
        if callable(self.user_setpoint.put_sleep):
            return self.user_setpoint.put_sleep()
        return self.user_setpoint.put_sleep

    @settle_time.setter
    def settle_time(self, val):
        self.user_setpoint.put_sleep = val

    @property
    def noise_func(self):
        if callable(self.user_readback.noise_func):
            return self.user_readback.noise_func()
        return self.user_readback.noise_func

    @noise_func.setter
    def noise_func(self, val):
        self.user_readback.noise_func = val

    @property
    def noise_type(self):
        return self.user_readback.noise_type

    @noise_type.setter
    def noise_type(self, val):
        self.user_readback.noise_type = val

    @property
    def noise_args(self):
        return self.user_readback.noise_args

    @noise_args.setter
    def noise_args(self, val):
        self.user_readback.noise_args = val

    @property
    def noise_kwargs(self):
        return self.user_readback.noise_kwargs

    @noise_kwargs.setter
    def noise_kwargs(self, val):
        self.user_readback.noise_kwargs = val


class OffsetMirror(SimDevice):
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
    # Pitch Motor
    pitch = FormattedComponent(OMMotor, "{self.prefix}")
    # Gantry Motors
    gan_x_p = FormattedComponent(OMMotor, "STEP:{self._mirror}:X:P")
    gan_y_p = FormattedComponent(OMMotor, "STEP:{self._mirror}:Y:P")

    # Placeholder signals for non-implemented components
    piezo = Component(FakeSignal)
    mps = Component(FakeSignal)
    state = Component(FakeSignal)

    # Simulation component
    sim_alpha = Component(FakeSignal)

    def __init__(self, prefix, prefix_xy,*, name=None, read_attrs=None,
                 parent=None, configuration_attrs=None, x=0, y=0, z=0, alpha=0, 
                 velo_x=0, velo_y=0, velo_z=0, velo_alpha=0, noise_x=0, 
                 noise_y=0, noise_z=0, noise_alpha=0, settle_time_x=0, 
                 settle_time_y=0, settle_time_z=0, settle_time_alpha=0, 
                 noise_func=None, noise_type="uni", noise_args=(), 
                 noise_kwargs={}, timeout=None, **kwargs):
        self._mirror = prefix_xy
        if len(prefix.split(":")) < 3:
            prefix = "MIRR:TST:{0}".format(prefix)
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent,
                         **kwargs)
        self.log_pref = "{0} (OffsetMirror) - ".format(self.name)

        # Simulation Attributes
        # Fake noise to readback and moves
        self.noise_x = noise_x
        self.noise_y = noise_y
        self.noise_z = noise_z
        self.noise_alpha = noise_alpha
        
        # Settle time for every move
        self.settle_time_x = settle_time_x
        self.settle_time_y = settle_time_y
        self.settle_time_z = settle_time_z
        self.settle_time_alpha = settle_time_alpha

        # Velocity for every move
        self.velo_x = velo_x
        self.velo_y = velo_y
        self.velo_z = velo_z
        self.velo_alpha = velo_alpha
        
        # Set initial position values
        self.gan_x_p.set(x)
        self.gan_y_p.set(y)
        self.sim_z.set(z)
        self.pitch.set(alpha)

        # Noise parameters
        self.noise_func = noise_func
        self.noise_type = noise_type
        self.noise_args = noise_args
        self.noise_kwargs = noise_kwargs

        # Simulation values
        self.sim_x._get_readback = lambda : self.gan_x_p.position
        self.sim_y._get_readback = lambda : self.gan_y_p.position
        self.sim_z.put(z)
        self.sim_alpha._get_readback = lambda : self.pitch.position

    def move(self, position, wait=False, **kwargs):
        return self.pitch.move(position, wait=wait, **kwargs)

    set = move

    @property
    def position(self):
        return self.pitch.position

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
    
    @property
    def noise_x(self):
        return self.gan_x_p.noise

    @noise_x.setter
    def noise_x(self, val):
        self.gan_x_p.noise = bool(val)

    @property
    def noise_y(self):
        return self.gan_y_p.noise

    @noise_y.setter
    def noise_y(self, val):
        self.gan_y_p.noise = bool(val)

    @property
    def noise_z(self):
        return self.sim_z.noise

    @noise_z.setter
    def noise_z(self, val):
        self.sim_z.noise = bool(val)

    @property
    def noise_alpha(self):
        return self.pitch.noise

    @noise_alpha.setter
    def noise_alpha(self, val):
        self.pitch.noise = bool(val)
    
    @property
    def settle_time_x(self):
        return self.gan_x_p.settle_time

    @settle_time_x.setter
    def settle_time_x(self, val):
        self.gan_x_p.settle_time = val

    @property
    def settle_time_y(self):
        return self.gan_y_p.settle_time

    @settle_time_y.setter
    def settle_time_y(self, val):
        self.gan_y_p.settle_time = val

    @property
    def settle_time_z(self):
        return self.sim_z.put_sleep

    @noise_z.setter
    def settle_time_z(self, val):
        self.sim_z.put_sleep = val

    @property
    def settle_time_alpha(self):
        return self.pitch.settle_time

    @settle_time_alpha.setter
    def settle_time_alpha(self, val):
        self.pitch.settle_time = val

    @property
    def velocity_x(self):
        return self.gan_x_p.velocity.value

    @velocity_x.setter
    def velocity_x(self, val):
        self.gan_x_p.velocity.value = val

    @property
    def velocity_y(self):
        return self.gan_y_p.velocity.value

    @velocity_y.setter
    def velocity_y(self, val):
        self.gan_y_p.velocity.value = val

    @property
    def velocity_z(self):
        return self.sim_z.velocity

    @velocity_z.setter
    def velocity_z(self, val):
        self.sim_z.velocity = val

    @property
    def velocity_alpha(self):
        return self.pitch.velocity.value

    @velocity_alpha.setter
    def velocity_alpha(self, val):
        self.pitch.velocity.value = val

    @property
    def noise_func(self):
        if callable(self.pitch.noise_func):
            return self.pitch.noise_func()
        return self.pitch.noise_func

    @noise_func.setter
    def noise_func(self, val):
        self.gan_x_p.noise_func = val
        self.gan_y_p.noise_func = val
        self.sim_z.noise_func = val
        self.pitch.noise_func = val

    @property
    def noise_type(self):
        return self.pitch.noise_type

    @noise_type.setter
    def noise_type(self, val):
        self.gan_x_p.noise_type = val
        self.gan_y_p.noise_type = val
        self.sim_z.noise_type = val
        self.pitch.noise_type = val

    @property
    def noise_args(self):
        return self.pitch.noise_args

    @noise_args.setter
    def noise_args(self, val):
        self.gan_x_p.noise_args = val
        self.gan_y_p.noise_args = val
        self.sim_z.noise_args = val
        self.pitch.noise_args = val

    @property
    def noise_kwargs(self):
        return self.pitch.noise_kwargs

    @noise_kwargs.setter
    def noise_kwargs(self, val):
        self.gan_x_p.noise_kwargs = val
        self.gan_y_p.noise_kwargs = val
        self.sim_z.noise_kwargs = val
        self.pitch.noise_kwargs = val

