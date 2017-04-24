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

##########
# Module #
##########

class OneMirrorSystem(object):
    """
    System of a source, mirror and an imager.
    """
    def __init__(self, **kwargs):
        self._x0 = kwargs.get("x0", 0)
        self._xp0 = kwargs.get("xp0", 0)
        self._x1 = kwargs.get("x1", 0)
        self._d1 = kwargs.get("d1", 90.510)
        self._a1 = kwargs.get("a1", 0.0014)
        self._x2 = kwargs.get("x2", 0.0317324)
        self._d2 = kwargs.get("d2", 101.843)
        self._noise_x0 = kwargs.get("noise_x0", 0)
        self._noise_xp0 = kwargs.get("noise_xp0", 0)
        self._noise_x1 = kwargs.get("noise_x1", 0)
        self._noise_d1 = kwargs.get("noise_d1", 0)
        self._noise_a1 = kwargs.get("noise_a1", 0)
        self._noise_x2 = kwargs.get("noise_x2", 0)
        self._noise_d2 = kwargs.get("noise_d2", 0)
        self._fake_sleep_s_x =  kwargs.get("fake_sleep_s_x", 0)
        self._fake_sleep_s_xp =  kwargs.get("fake_sleep_s_xp", 0)
        self._fake_sleep_m1_x = kwargs.get("fake_sleep_m1_x", 0)
        self._fake_sleep_m1_z = kwargs.get("fake_sleep_m1_z", 0)
        self._fake_sleep_m1_alpha = kwargs.get("fake_sleep_m1_alpha", 0)
        self._fake_sleep_y1_x = kwargs.get("fake_sleep_y1_x", 0)
        self._fake_sleep_y1_z = kwargs.get("fake_sleep_y1_z", 0)
        self._name_s = kwargs.get("name_s", "Source")
        self._name_m1 = kwargs.get("name_m1", "Mirror 1")
        self._name_y1 = kwargs.get("name_y1", "YAG 1")
        self._pix_y1 = kwargs.get("pix_y1", (1392, 1040))
        self._size_y1 = kwargs.get("size_y1", (0.0076, 0.0062))
        self._invert_y1 = kwargs.get("invert_y1", False)

        self.source = Source(self._name_s, self._x0, self._xp0,
                             noise_x=self._noise_x0, noise_xp=self._noise_xp0,
                             fake_sleep_x=self._fake_sleep_s_x,
                             fake_sleep_xp=self._fake_sleep_s_xp)
        
        self.mirror_1 = Mirror(self._name_m1, self._x1, self._d1, self._a1,
                               noise_x=self._noise_x1, noise_alpha=self._noise_a1,
                               fake_sleep_x=self._fake_sleep_m1_x,
                               fake_sleep_z=self._fake_sleep_m1_z,
                               fake_sleep_alpha=self._fake_sleep_m1_alpha)

        self.yag_1 = YAG(self._name_y1, self._x2, self._d2, self._noise_x2,
                         self._noise_d2, pix=self._pix_y1, size=self._size_y1,
                         fake_sleep_x=self._fake_sleep_y1_x,
                         fake_sleep_z=self._fake_sleep_y1_z)
        
        self.yag_1._cent_x = self.calc_cent_x

    def calc_cent_x(self):
        x = OneBounce(self.mirror_1._alpha,
                      self.source._x,
                      self.source._xp,
                      self.mirror_1._x,
                      self.mirror_1._z,
                      self.yag_1._z)
        return np.round(np.floor(self.yag_1.pix[0]/2) + \
                        (1 - 2*self._invert_y1)*(x - self.yag_1._x) * \
                        self.yag_1.pix[0]/self.yag_1.size[0])


def OneBounce(a1, x0, xp0, x1, d1, d2):
    return -2*a1*d1 + 2*a1*d2 - d2*xp0 + 2*x1 - x0

def TwoBounce(alphas, x0, xp0, x1, d1, x2, d2, d3):
    return 2*alphas[0]*d1 - 2*alphas[0]*d3 - 2*alphas[1]*d2 + 2*alphas[1]*d3 + \
        d3*xp0 - 2*x1 + 2*x2 + x0

class Source(object):
    """
    Simulation of the photon source (simplified undulator).
    """
    def __init__(self, name, x, xp, noise_x, noise_xp, fake_sleep_x=0,
                 fake_sleep_xp=0):
        self.name = name
        self.noise_x = noise_x
        self.noise_xp = noise_xp
        self.fake_sleep_x = fake_sleep_x
        self.fake_sleep_xp = fake_sleep_xp
        self.x = Mover('X Motor', OrderedDict(
                [('x', lambda x: x + np.random.uniform(-1, 1)*self.noise_x),
                 ('x_setpoint', lambda x: x)]), {'x': x})
        self.xp = Mover('XP Motor', OrderedDict(
                [('xp', lambda xp: xp + np.random.uniform(-1, 1)*self.noise_xp),
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

class Mirror(object):
    """
    Simulation of the Flat Mirror Pitch

    Parameters
    ----------
    name : string
        Name of motor

    initial_position : float
        Initial x position of the motor in meters from nominal

    initial_pitch : float
        Initial pitch of motor in microradians

    distance : float
        Distance of the mirror from the source in meters

    noise_position : float, optional
        Scaler to multiply uniform noise on position 

    noise_pitch : float, optional
        Scaler to multiply uniform noise on pitch

    fake_sleep, float, optional
        Simulate moving time
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
                [('alpha', lambda alpha: alpha + \
                      np.random.uniform(-1, 1)*self.noise_alpha),
                 ('alpha_setpoint', lambda alpha: alpha)]), {'alpha': alpha},
                           fake_sleep=self.fake_sleep_alpha)
        self.motors = [self.x, self.z, self.alpha]
        self._x = x
        self._z = z
        self._alpha = alpha        

    def read(self):
        return dict(ChainMap(*[motor.read() for motor in self.motors]))

    def set(self, **kwargs):
        self._x = kwargs.get('x', self._x)
        self._z = kwargs.get('z', self._z)
        self._alpha = kwargs.get('alpha', self._alpha)
        for key in kwargs.keys():
            for motor in self.motors:
                if key in motor.read():
                    motor.set(kwargs[key])
        
class YAG(object):
    """
    Simulation of a single bounce YAG

    The model makes the assumption that we have a single mirror and a
    downstream YAG, whose edge is left edge is hit when the position of the
    motor is zero.

    Parameters
    ----------
    name : str
        Alias of YAG

    motor : Positioner
        Simulated pitch of mirror

    motor_field : str
        Name of motor_field to calculate centroid position. Value should be
        expressed in microns

    distance : float
        Distance from mirror to YAG in meters

    inverted : bool, optional
        Whether the image is reflected before being imaged by the camera

    noise_multiplier : float, optional
        Introduce unifrom random noise to the pixel location
    """
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
        self.pix = kwargs.get("pix", (1392, 1040))
        self.size = kwargs.get("size", (0.0076, 0.0062))        
        self.reader = Reader(self.name, {'centroid_x' : self.cent_x,
                                         'centroid_y' : self.cent_y,
                                         'centroid' : self.cent})        
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
                             
    def read(self):
        return dict(ChainMap(*[dev.read() for dev in self.devices]))

    def set(self, **kwargs):
        self._x = kwargs.get('x', self._x)
        self._z = kwargs.get('z', self._z)
        for key in kwargs.keys():
            for motor in self.motors:
                if key in motor.read():
                    motor.set(kwargs[key])
                                        
if __name__ == "__main__":
    sys = OneMirrorSystem()
    m = sys.mirror_1
    # print("x: ", m.read()['x']['value'])
    # m.set(x=10)
    # print("x: ", m.read()['x']['value'])

    y = sys.yag_1
    # import ipdb; ipdb.set_trace()
    pprint(y.read()['centroid_x']['value'])

    m.set(x=0.035)
    pprint(y.read()['centroid_x']['value'])
    
    # import IPython; IPython.embed()
    # print("Centroid:", system.yag_1.read()['centroid_x']['value'])
