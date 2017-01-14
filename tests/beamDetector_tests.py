import numpy as np
import beamDetector.detector as bd
from nose.tools import *
from utils.cvUtils import  get_images_from_dir

# test_images_01_dir = "tests/test_yag_images_01/"
# test_images_01 = get_images_from_dir(test_images_01_dir)
# image = test_images_01[0]
# det = bd.Detector()

class TestDetector(object):
    @classmethod
    def setup_class(self):
        self.test_images_01_dir = "tests/test_yag_images_01/"
        self.test_images_01 = get_images_from_dir(self.test_images_01_dir)
        self.image = self.test_images_01[0]
        self.det = bd.Detector()

    def test_preprocess_image_type(self):
        preprocessed_image = self.det.preprocess(self.image)
        assert_equals(preprocessed_image.dtype, np.uint8)

    def test_get_contours(self):
        preprocessed_image = self.det.preprocess(self.image)
        contour = self.det.get_contour(preprocessed_image)
        assert isinstance(contour, np.ndarray)
        assert_equals(contour.shape[1:], (1,2))
    
    def test_get_moments(self):
        preprocessed_image = self.det.preprocess(self.image)
        contour = self.det.get_contour(preprocessed_image)
        M = self.det.get_moments(contour=contour)
        assert isinstance(M, dict)
        assert_equals(len(M), 24)

    def test_beam_is_present_type(self):
        preprocessed_image = self.det.preprocess(self.image)
        contour = self.det.get_contour(preprocessed_image)
        M = self.det.get_moments(contour=contour)
        assert isinstance(self.det.beam_is_present(M), bool)

    def test_centroid(self):
        preprocessed_image = self.det.preprocess(self.image)
        contour = self.det.get_contour(preprocessed_image)
        M = self.det.get_moments(contour=contour)
        centroid = self.det.get_centroid(M)
        assert isinstance(centroid, tuple)
        assert isinstance(centroid[0], int)
        assert_equals(len(centroid), 2)

    


