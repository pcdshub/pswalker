import cv2
import numpy as np
from joblib import Memory
from tqdm import tqdm
from ast import literal_eval
from multiprocessing import Process
from psp import Pv as pv

from blbase import motor, iterscan

from utils.cvUtils import to_uint8

from __future__ import print_function

from scipy.optimize import minimize

cachedir = "cache"
mem = Memory(cachedir=cachedir, verbose=0)


################################################################################
#                                  Focus Class                                 #
################################################################################


class Focus(object):
    """
    Base focusing class that will determine the focus over a range of values and
    then return the value that had the highest focus.

    Kwargs:
        resize (float): Resize factor (1.0 keeps image same size).
        kernel (tuple): Tuple of length 2 for gaussian kernel size.
        sigma (int): Gaussian std in x and y. Set 0 to compute internally.

    """
    
    def __init__(self, motor_pv, positions, camera_pv, **kwargs):

        self.motor_pv   = motor_pv
        self.positions  = positions
        self.camera_pv  = cameraPv

        self._check_arguments()
        
        self.resize          = kwargs.get("resize", 1.0)
        self.kernel          = kwargs.get("kernel", (17,17))
        self.sigma           = kwargs.get("kernel", 0)
        self.average         = kwargs.get("average", 1)
        self.method          = kwargs.get("method", "scan")
        self.sharpness       = kwargs.get("sharpness", "laplacian")
        
        self._focus_methods         = dict("scan"      : self._scan_focus,
                                           "hillclimb" : self._hillclimb_focus)
        self._sharpness_methods      = dict("sobel"     : self._sobel_var, 
                                            "laplacian" : self._laplacian_var)
        self.best_pos   = None
        self.best_focus = 0

        self._motors      = self._get_motor_objs()
        self._motor_iters = self._get_motor_iters()

    def _check_arguments(self):
        if isinstance(self.motor_pv, basestring):
            assert_equals(len(self.positions), 3)
        elif isiterable(self.motor_pv):
            assert_equals(len(self.positions), len(self.motor_pv))
            for pv, pos in zip(self.motor_pv, self.positions):
                assert isinstance(pv, basestring)
                assert isiterable(pos)
                assert_equals(len(pos), 3)
        assert isinstance(self.camera_pv, basestring)

    def _get_motor_objs(self):
        motors = []
        if isinstance(self.motor_pv, basestring):
            motors.append(Motor(self.motor_pv, name = pv.get(
                self.motor_pv+".DESC")))
        elif isiterable(self.motor_pv):
            for pv in self.motor_pv:
                motors.append(VirtualMotor(pv))
        return tuple(motors)
        
    def _get_motor_iters(self):
        pos_list = []
        # This is most likely incorrect. Check this first if things go wrong
        if isiterable(self.positions[0]):
            for pos in self.positions
                pos_list.append(range(*pos))
            pos_list = zip(*pos_list)
        else:
            pos_list = range(*self.positions)
        return iter(pos_list)

    def preprocess(self, image):
        """Preprocess the image by resizing and running a gaussian blur. 

        Args:
            image (np.ndarray): The image to be preprocessed.
        Returns:
            np.ndarray. Preprocessed Image.
    
        Depending on the specific use case this method should be overwritten to
        implement the necessary preprocessing pipeline.
        """
        image = to_uint8(image)
        image_small = cv2.resize(image, (0,0), fx=self.resize, fy=self.resize)
        image_gblur = cv2.GaussianBlur(image_small, self.kernel, self.sigma)
        # Look into histogram equalization
        return image_gblur

    def get_image(self, cameraPv=None):
        if cameraPv:
            self.cameraPv = cameraPv
        return pv.get(cameraPv)

    def _laplacian_var(self, image):
        return cv2.Laplacian(image, cv2.CV_64F).var()

    def _sobel_var(self, image, ksize=5):
        sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=ksize).var()
        sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=ksize).var()
        return sobel_x/2.0 + sobel_y/2.0
    
    def get_focus(self, image, sharpness="laplacian", const=1):
        image_prep = self.preprocess(image)
        return const * self._sharpness_methods[sharpness.lower()](image)

    def get_ave_focus(self, sharpness="laplacian"):
        focus = np.empty([self.average])
        for i in range(self.average):
            image = self.get_image()
            focus[i] = self.get_focus(image, sharpness=sharpness)
        return focus.mean()
    
    def _scan_focus(self):
        scan = IterScan(self, self._motors, self._motor_iters)
        scan.scan_mesh()
        return self.best_pos

    def _move_and_focus(self, position):
        self._motors.mv(position)
        self._motors.wait()
        return self._get_ave_focus()

    def _hillclimb_focus(self, method="BFGS"):
        self.best_pos = minimize(self._move_and_focus, self._motors.wm(), 
                                 method=method)
        return self.best_pos
    
    def focus(self, method="scan", sharpness="laplacian"):
        if method != self.method:
            self.method = method
        if sharpness != self.sharpness:
            self.sharpness = sharpness
        return self._focus_methods[self.method.lower()]()

    def pre_focus_hook(self, current_image, current_position):
        pass
    
    def post_focus_hook(self, current_image, current_position, current_focus):
        pass

    # Methods required for this class to function as an IterScan hook
    def pre_step(self, scan):
        pass

    def post_step(self, scan):
        current_pos = self.positions.next()
        self.pre_focus_hook(image, current_pos)

        focus = get_ave_focus()

        if focus > self.best_focus:
            self.best_focus = focus
            self.best_pos = current_pos

        self.post_focus_hook(image, current_pos, focus)

    def pre_scan(self, scan):
        pass

    def post_scan(self, scan):
        print("Scan completed. \nBest focus found at: {0}".format(
            self.best_pos))


class VirtualMotor(object):
    """Virtual motor class until the real one works."""
    def __init__(self, motors):
        self._motor_pvs = motors
        self._motors   = self._get_motors(self._motor_pvs)
        self.num_motors = len(self._motors)
        self.name      = ""
        for motor in self._motors:
            self.name += motor.name + "+"
        self.name = self.name[:-1]
    def _get_motors(self, motor_pvs):
        motor_names = [pv.get(motor_pv + ".DESC") for motor_pv in motor_pvs]
        return [Motor(motor, name=motor_name) for motor, motor_name in zip(
            motor_pvs, motor_names)]
    def mv(self, vals):
        if len(val) == len(self._motors):
            for motor, val in zip(self._motors, vals):
                motor.mv(val)
        else:
            raise ValueError("Motor and position mismatch: {0} motors with {1} \
inputted motions.".format(len(self._motors), len(vals)))
    def wm(self):
        return [motor.wm() for motor in self._motors]
    def wait(self):
        for motor in self._motors:
            motor.wait()

def isiterable(obj):
    """
    Function that determines if an object is an iterable, but not including 
    strings.
    """
    if isinstance(obj, basestring):
        return False
    else:
        return isinstance(obj, Iterable)

        
    # def find_focus(self, iter_func, iter_args, method="laplacian"):
    #     best_arg = None
    #     best_focus = 0
    #     for iter_arg in iter_args:
    #         image = iter_func(iter_arg)
    #         focus = self.get_focus(image, method=method)
    #         if focus > best_focus:
    #             best_focus = focus
    #             best_arg = iter_arg
    #     iter_func(best_arg)
    

# class focus_hooks(object):

#     def __init__(self, focuser, positions, method="laplacian"):
#         self.focuser    = focuser
#         self.positions  = positions
#         self.method     = method
    
#     def pre_step(self, scan):
#         pass
#     def post_step(self, scan):
#         current_pos = positions.next()
#         image = self.focuser.get_image()
        
#         self.focuser.pre_focus_hook()

#         focus = self.focuser.get_focus(image, self.method)
            
#         if focus > self.best_focus:
#             self.focuser.best_focus = focus
#             self.focuser.best_pos = current_pos

#         self.focuser.post_focus_hook()
#     def pre_scan(self, scan):
#         pass
#     def post_scan(self, scan):
#         print("Scan completed. \nBest focus found at: {0}".format(
#             self.focuser.best_pos))
