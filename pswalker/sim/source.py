from ophyd.device import Component

from .sim import SimDevice
from .signal import FakeSignal


class Undulator(SimDevice):
    """
    Simulated undulator ophyd object.
    """
    sim_xp = Component(FakeSignal, value=0)
    sim_yp = Component(FakeSignal, value=0)
    def __init__(self, prefix, *, x=0, xp=0, y=0, yp=0, z=0, velo_x=0, velo_xp=0,
                 velo_y=0, velo_yp=0, velo_z=0, noise_x=False, noise_xp=False, 
                 noise_y=False, noise_yp=False, noise_z=False, settle_time_x=0,
                 settle_time_xp=0, settle_time_y=0, settle_time_yp=0, 
                 settle_time_z=0, noise_func=None, noise_type="uni", 
                 noise_args=(), noise_kwargs={}, **kwargs):
        super().__init__(prefix, **kwargs)
        self.log_pref = "{0} (Undulator) - ".format(self.name)
        # Simulation Attributes
        # Initial Values
        self.sim_x.put(x)
        self.sim_xp.put(xp)
        self.sim_y.put(y)
        self.sim_yp.put(yp)
        self.sim_z.put(z)
        # Velocity for every move
        self.sim_x.velocity = velo_x
        self.sim_xp.velocity = velo_xp
        self.sim_y.velocity = velo_y
        self.sim_yp.velocity = velo_yp
        self.sim_z.velocity = velo_z
        # Fake noise to readback and moves
        self.sim_x.noise = noise_x
        self.sim_xp.noise = noise_xp
        self.sim_y.noise = noise_y
        self.sim_yp.noise = noise_yp
        self.sim_z.noise = noise_z        
        # Settle time for every move
        self.sim_x.put_sleep = settle_time_x
        self.sim_xp.put_sleep = settle_time_xp
        self.sim_y.put_sleep = settle_time_y
        self.sim_yp.put_sleep = settle_time_yp
        self.sim_z.put_sleep = settle_time_z
        # Noise type to use
        self.sim_x.noise_type = noise_type
        self.sim_xp.noise_type = noise_type
        self.sim_y.noise_type = noise_type
        self.sim_yp.noise_type = noise_type
        self.sim_z.noise_type = noise_type
        # Noise args for the noise function
        self.sim_x.noise_args = noise_args
        self.sim_xp.noise_args = noise_args
        self.sim_y.noise_args = noise_args
        self.sim_yp.noise_args = noise_args
        self.sim_z.noise_args = noise_args
        # Noise kwargs for the noise function
        self.sim_x.noise_kwargs = noise_kwargs
        self.sim_xp.noise_kwargs = noise_kwargs
        self.sim_y.noise_kwargs = noise_kwargs
        self.sim_yp.noise_kwargs = noise_kwargs
        self.sim_z.noise_kwargs = noise_kwargs
