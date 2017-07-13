#!/usr/bin/env python
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
from psbeam.preprocessing import uint_resize_gauss
from psbeam.beamexceptions import NoContoursPresent
from psbeam.contouring import (get_largest_contour, get_moments, get_centroid,
                               get_circularity)

##########
# Module #
##########

logger = logging.getLogger(__name__)

def psbeam_full_check(image, centroids_ad, resize=1.0, kernel=(13,13),
                      n_opening=2, cent_rtol=0.1, threshold_m00_min=50,
                      threshold_m00_max=10e6, threshold_circularity=0.067):
    """
    Runs the full pipeline which includes:
        - Checks if there is beam by obtaining an image contour
        - Checks the sum of all pixels is above and below a threshold
        - Checking if the computed centroid is close to the adplugin centroid
        - Checks that the beam is above the threshold of circularity

    Parameters
    ----------
    image : np.ndarray
        Image to process

    centroids_ad : tuple
        Centroids obtained from the areadetector stats plugin.

    resize : float, optional
        Resize the image before performing any processing.

    kernel : tuple, optional
        Size of kernel to use when running the gaussian filter.

    n_opening : int, optional
        Number of times to perform an erosion, followed by the same number of
        dilations.

    cent_rtol : float, optional
        Relative tolerance to use when comparing AD's and OpenCV's centroids.

    threshold_m00_min : float, optional
        Lower threshold for the sum of pixels in the image.

    threshold_m00_max : float, optional
        Upper threshold for the sum of pixels in the image.

    threshold_cicularity : float, optional
        Upper threshold for beam circularity score (0.0 is perfectly circular).

    Returns
    -------
    bool
        Bool indicating whether the image passed the tests.
    """
    try:
        # # Pipeline
        # Preprocessing
        image_prep = uint_resize_gauss(image, fx=resize, fy=resize, 
                                       kernel=kernel)
        # Morphological Opening
        image_morph = get_opening(image_prep, n_erode=n_opening, 
                                  n_dilate=n_opening)
        # Grab the image contours
        _, contours, _ = cv2.findContours(image_morph, 1, 2)
        # Grab the largest contour
        contour, area = get_largest_contour(image_prep, contours=contours)
        # Image moments
        M = get_moments(contour=contour)
        # Find a centroid
        centroids_cv = [pos//resize for pos in get_centroid(M)]
        # Get a score for how similar the beam contour is to a circle's contour
        circularity = get_circularity(contour)
        
        # # Filters
        # Sum of pixel intensities must be between m00_min and m00_max
        if M['m00'] < threshold_m00_min or M['m00'] > threshold_m00_max:
            logger.debug("Filter - Image sum ouside specified range. Sum: " \
                         "{0}".format(M['m00']))
            return False
        
        # The centroids of both ad and cv must be close
        for cent_ad, cent_cv in zip(centroids_ad, centroids_cv):
            if not np.isclose(cent_ad, cent_cv, rtol=cent_rtol):
                logger.debug("Filter - AD and OpenCV centroids not close. " \
                             "AD Centroid: {0} OpenCV Centroid: {1}".format(
                                 centroids_ad, centroids_cv))
                return False
            
        # Check that the circularity of the beam is below the inputted threshold
        if circularity > threshold_circularity:
            logger.debug("Filter - Beam cicularity too low. Cicularity: "
                         "{0}".format(circularity))
            return False
        
        # Everything passes
        return True
    
    except NoContoursPresent:
        # Failed to get image contours
        logger.debug("Filter - No contours found on image.")
        return False
