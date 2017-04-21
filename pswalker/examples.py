############
# Standard #
############
from collections import OrderedDict, ChainMap
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
        self._fake_sleep_s =  kwargs.get("fake_sleep_s", 0)
        self._fake_sleep_m1 = kwargs.get("fake_sleep_m1", 0)
        self._name_s = kwargs.get("name_s", "Source")
        self._name_m1 = kwargs.get("name_m1", "Mirror 1")
        self._name_y1 = kwargs.get("name_y1", "YAG 1")
        self._pix_y1 = kwargs.get("pix_y1", (1392, 1040))
        self._size_y1 = kwargs.get("size_y1", (0.0076, 0.0062))
        self._inverted_y1 = kwargs.get("inverted_y1", False)

        self.source = Source(self._name_s, self._x0, self._xp0,
                             noise_x=self._noise_x0, noise_xp=self._noise_xp0,
                             fake_sleep=self._fake_sleep_s)
        
        self.mirror_1 = Mirror(self._name_m1, self._x1, self._d1, self._a1,
                               noise_x=self._noise_x1, noise_alpha=self._noise_a1,
                               fake_sleep=self._fake_sleep_m1)

        self.yag_1 = YAG(self._name_y1, self._x2, self._d2, self._noise_x2,
                         self._noise_d2, pix=self._pix_y1, size=self._size_y1)
        
        def calc_cent_x():
            x = -2*self.mirror_1.alpha*self.mirror_1.z + \
              2*self.mirror_1.alpha*self.yag_1.z - \
              self.yag_1.z*self.source.xp + 2*self.mirror_1.x - self.source.x
            return np.floor(self.yag_1.pix[0]/2) + \
                (x - self.x2)*self.yag_1.pix[0]/self.yag_1.size[0]
            
        self.yag_1.cent_x = calc_cent_x

class Source(Mover):
    """
    Simulation of the photon source (simplified undulator).
    """
    def __init__(self, name, x, xp, noise_x, noise_xp, fake_sleep=0):
        self.name = name
        self.x = x
        self.xp = xp
 
        def position(**kwargs):
            x = kwargs['x']
            if noise_x:
                x += np.random.uniform(-1, 1)*noise_x
            self.x = x
            return self.x
        
        def pointing(**kwargs):
            xp = kwargs['xp']
            if noise_xp:
                xp += np.random.uniform(-1, 1)*noise_xp
            self.xp = xp
            return self.xp
        # import ipdb; ipdb.set_trace()
        super().__init__(
            self.name, OrderedDict(
                [('x', position),
                ('xp', pointing),
                ('x_setpoint', lambda **kwargs: kwargs['x']),
                ('xp_setpoint', lambda **kwargs: kwargs['xp'])]),
            {'x':self.x, 'xp':self.xp}, fake_sleep=fake_sleep)


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
                 noise_alpha=0, fake_sleep=0):
        self.name = name
        self.x = Mover('X Motor', OrderedDict(
                [('x', lambda x: x + np.random.uniform(-1, 1)*noise_x),
                 ('x_setpoint', lambda x: x)]), {'x': x})
        self.z = Mover('Z Motor', OrderedDict(
                [('z', lambda z: z + np.random.uniform(-1, 1)*noise_z),
                 ('z_setpoint', lambda z: z)]), {'z': z})
        self.alpha = Mover('Alpha Motor', OrderedDict(
                [('alpha', lambda alpha: alpha + np.random.uniform(-1, 1)*noise_alpha),
                 ('alpha_setpoint', lambda alpha: alpha)]), {'alpha': alpha})
        self.noise_x = noise_x
        self.noise_z = noise_z
        self.noise_alpha = noise_alpha
        self.motors = [self.x, self.z, self.alpha]

    def read(self):
        return dict(ChainMap(*[motor.read() for motor in self.motors]))

    def set(self, **kwargs):
        for key in kwargs.keys():
            for motor in self.motors:
                if key in motor.read():
                    motor.set(kwargs[key])
        
class YAG(Reader):
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
    def __init__(self, name, x, z, noise_x, noise_z, **kwargs):
        
        self.name = name
        self._x = x
        self.z = z
        self.noise_x = noise_x
        self.noise_z = noise_z

        self.pix = kwargs.get("pix", (1392, 1040))
        self.size = kwargs.get("size", (0.0076, 0.0062))

        def position(**kwargs):
            x = kwargs['x']
            if noise_x:
                x += np.random.uniform(-1, 1)*noise_x
            self._x = x
            return self._x
        
        def distance(**kwargs):
            z = kwargs['z']
            if noise_z:
                z += np.random.uniform(-1, 1)*noise_z
            self.z = z
            return self.z
               
        def cent_x():
            return np.floor(self.pix[0]/2)
        
        def cent_y():
            return np.floor(self.pix[1]/2)

        def cent():
            return (cent_x(), cent_y())

        self.motor = Mover(self.name+" Motor",
                           {'x': position,
                            'x_setpoint':lambda **kwargs : kwargs['x']},
                           {'x':self._x})

        super().__init__(self.name, {'centroid_x' : cent_x,
                                     'centroid_y' : cent_y,
                                     'centroid' : cent})

    @property
    def x(self):
        return self.motor.read()['x']['value']
    
    @x.setter
    def x(self, val):
        self.motor.set(val)

                                        
if __name__ == "__main__":
    sys = OneMirrorSystem()
    m = sys.mirror_1
    print("x: ", m.read()['x']['value'])
    m.set(x=10)
    print("x: ", m.read()['x']['value'])
    import IPython; IPython.embed()
    # print("Centroid:", system.yag_1.read()['centroid_x']['value'])
