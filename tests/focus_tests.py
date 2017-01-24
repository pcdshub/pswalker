import numpy as np
import autoFocus.focus as af
from nose.tools import *
from utils.cvUtils import  get_images_from_dir

class TestDetector(object):
    @classmethod
    def setup_class(self):
        self.image = cv2.imread("tests/test_yag_images_01/image01.jpg", 
                                cv2.IMREAD_GRAYSCALE)
    def test_correctness_1(self):
        
        




class VirtualMotorTest(af.VirtualMotor):
    """Virtual motor class until the real one works."""
    def __init__(self, image, const=0):
        self.image = image
    def mv(self, pos):
	    self.cur_position = pos
    def wm(self):
        return self.cur_position
    def wait(self):
	    pass

class VirtualCameraTest(af.VirtualCamera):
    """Virtual camera class until one is found/implemented."""
    def __init__(self, motor, const=0):
        self.motor
        self.const = const
    def get(self):
        kernel = np.ceil(abs(self.motor.wm())) + const
        return cv2.GaussianBlur(image_small, (kernel, kernel), 0)
	
