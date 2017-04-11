"""
Hardware components used by walker that *should* be implemented as ophyd
devices.
"""

import utils.exceptions as uexc

from ophyd import Device, EpicsMotor # Or another ophyd motor implementation
from beamDetector.detector import Detector
from utils.cvUtils import to_uint8, plot_image
from utils.exceptions import ComponentException

################################################################################
#                                 Imager Class                                 #
################################################################################

class Imager(Device):
    """
    Imager object that will encapsulate the various yag screens along the
    beamline. 
    """
    # If we have an implementation of an imager we should inherit form it and
    # just add the couple image processing methods used here.
    def __init__(self, **kwargs):
        self.detector = kwargs.get("det", Detector(prep_mode="clip"))
        self.image    = None
        self.image_xsz = 0
        self.image_ysz = 0
        self.centroid = None
        self.bounding_box = None
        self.beam = False
        self.inserted = False
        self.mppix = kwargs.get("mppix", 1.25e-5) # meters per pixel
        self.pv_camera = kwargs.get("camera", None)
        self.simulation = kwargs.get("simulation", False)

    def get_image(self, norm="clip"):
        """Get a new image from the imager."""
        if self.simulation:
            try:
                uint_norm = to_uint8(self.image, "norm")
                self.image_ysz, self.image_xsz  = self.image.shape
                return to_uint8(uint_norm, "clip")
            except TypeError:
                self.sum = self.image.sum()
                return self.get_image(norm=norm)
        else:
            self.image = to_uint8(caget(self.pv_camera), norm)
            return self.image

    def get_beam(self, norm="clip", cent=True, bbox=True):
        """Return beam info (centroid and bounding box) of the saved image."""
        try:
            self.centroid, self.bounding_box = self.detector.find(self.image)
            self.beam = True
            if cent and bbox:
                return self.centroid, self.bounding_box
            elif cent:
                return self.centroid
            elif bbox:
                return self.bounding_box
            else:
                raise ComponentException
        except IndexError:
            self.beam = False
            return None
        
    def get_centroid(self, norm="clip"):
        """Return the centroid of the stored image."""
        return self.get_beam(norm, cent=True, bbox=False)

    def get_bounding_box(self, norm="clip"):
        """Return the bounding box of the stored image."""
        return self.get_beam(norm, cent=False, bbox=True)
        
    def get_image_and_centroid(self, norm="clip"):
        """Get a new image and return the centroid."""
        self.get_image(norm)
        return self.get_centroid(self, norm)

    def get_image_and_bounding_box(self, norm="clip"):
        """Get a new image and return the bounding box."""
        self.get_image(norm)
        return self.get_bounding_box(self, norm)

    def get_image_and_beam(self, norm="clip"):
        """Get a new image and return both the centroid and bounding box."""
        self.get_image(norm)
        return self.get_beam(self, norm)

    def insert(self):
        """Moves the yag to the inserted position."""
        # This will be filled in with lightpath functions/methods.
        raise NotImplementedError
    
    def remove(self):
        """Moves the yag to the removed position."""
        # This will be filled in with lightpath functions/methods.
        raise NotImplementedError

################################################################################
#                                 Mirror Class                                 #
################################################################################

class FlatMirror(Device):
    """
    Mirror class to encapsulate the two HOMS (or any) mirrors.
    """
    def __init__(self, **kwargs):
        # As a first pass implementation, the x and alpha motors are just
        # epics motors and z is just a simple attribute to hold the z position
        # of the mirror.
        self.mot_x       = EpicsMotor(kwargs.get("x", None),name="X Mot")
        self.mot_alpha   = EpicsMotor(kwargs.get("alpha", None),name="Pitch Mot")
        # self.z           = kwargs.get("z", None) # This is 
        # self.x_pv        = kwargs.get("x_pv", None)
        # self.alpha_pv    = kwargs.get("alpha_pv", None)
        # self.simulation  = kwargs.get("simulation", True)
        # self.pos         = np.array([self.z, self.x])


                                      
        # self._check_args()
        # if self._x is None and not self.simulation:
        #     self.x = caget(self.x_pv) + self.x_offset

#     def _check_args(self):
#         # Only allowed to set alpha in sim mode
#         if self.alpha is not None and not self.simulation:
#             raise uexc.ImagerInputError(
#                 "Can only set alpha in simulation mode.")
#         # Must set x motor pv if not in sim mode. Warning if set in sim mode.
#         if self.x_pv is None and not self.simulation:
#             raise uexc.ImagerInputError(
#                 "Must input x motor pv when not in simulation mode.")
#         elif self.x_pv and self.simulation:
#             warnings.warn("Ignoring input - X motor pv inputted when simulation \
# mode is active.")
#         # Must set alpha motor pv not in sim mode. Warning if set in sim mode.
#         if self.alpha_pv is None and not self.simulation:
#             raise uexc.ImagerInputError(
#                 "Must input alpha motor pv when not in simulation mode.")
#         elif self.alpha_pv and self.simuation:
#             warnings.warn("Ignoring input - alpha motor pv inputted when \
# simulation mode is active.")

    @property
    def x(self):
        return self.mot_x.position
        
    @x.setter
    def x(self, x, **kwargs):
        self.mot_x.move(val, **kwargs)

    @property
    def alpha(self):
        return self.mot_alpha.position
        
    @alpha.setter
    def alpha(self, alpha, **kwargs):
        self.mot_alpha.move(val, **kwargs)
        

################################################################################
#                                 Source Class                                 #
################################################################################

class Linac(Device):
    def __init__(self, **kwargs):
        # I believe there is a Linac class somewhere in blinst but I don't know
        # how well it works or it is something we even want to use. It could be
        # too low level for what we trying to do.
        self.mot_x = EpicsMotor(kwargs.get("x", None),name="X Mot")
        self.mot_xp = EpicsMotor(kwargs.get("xp", None),name="X Pointing Mot")
        
    @property
    def x(self):
        return self.mot_x.position
        
    @x.setter
    def x(self, x, **kwargs):
        self.mot_x.move(val, **kwargs)

    @property
    def xp(self):
        return self.mot_xp.position
        
    @xp.setter
    def xp(self, xp, **kwargs):
        self.mot_xp.move(val, **kwargs)
