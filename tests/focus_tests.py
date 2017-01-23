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
        
        




class VirtualMotor(object):
    """Virtual motor class until the real one works."""
    def __init__(self, image, const=0):
        self.image = image
        self.cur_position = 0
        self.const = const

    def mv(self, blur):
	    self.cur_position = blur
	    kernel = np.ceil(abs(blur)) + const
	    return cv2.GaussianBlur(image_small, (kernel, kernel), 0)
        
    def wm(self):
        return self.cur_position

    def wait(self):
	    pass
