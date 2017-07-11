"""
Signal filters used in Skywalker.
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
import cv2
import numpy as np
from psbeam.morph import get_opening
from psbeam.beamexceptions import (NoContoursPresent, NoBeamPresent)
from psbeam.contouring import (get_largest_contour, get_moments, get_centroid)

##########
# Module #
##########

logger = logging.getLogger(__name__)

def psbeam_full_check(image, centroids_ad, resize=1.0, kernel=(13,13),
                      n_opening=2, m00_min=50, m00_max=10e4, cent_rtol=0.2):
    """
    Runs the full pipeline which includes:
    	- Checks the sum of all pixels is above a threshold
    	- Checking if the computed centroid is close to the adplugin centroid
    """
    try:
        # Preprocessing
        image_prep = uint_resize_gauss(image, resize=resize, kernel=kernel)
        # Morphological Opening
        image_morph = get_opening(image_prep, erode=n_opening, dilate=n_opening)
        # Grab the image contours
        _, contours, _ = cv2.findContours(image_morph, 1, 2)
        # Grab the largest contour
        contour, area = psb.get_largest_contour(image_prep, contours=contours, 
                                                get_area=True)
        # Image moments
        M = psb.get_moments(contour=contour)
        # Find a centroid
        centroids_cv = [pos//resize for pos in get_centroid(M)]
        
        # # Filters
        # Sum of pixel intensities must be between m00_min and m00_max
        if M['m00'] < m00_min or M['m00'] > m00_max:
            return False

        # Check the centroids of both ad and cv more or less agree
        for cent_ad, cent_cv in zip(centroids_ad, centroids_cv):
            if not np.isclose(cent_ad, cent_cv, rtol=cent_rtol):
                return False        

        # Everything passes
        return True
    
    except NoContoursPresent:
        # Failed to get image contours
        return False
