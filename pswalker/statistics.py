"""
Beam statistics plans
"""
############
# Standard #
############
import logging
import time
from copy import copy

###############
# Third Party #
###############
import numpy as np
from bluesky.plans import checkpoint
from psbeam.utils import signal_tuple
from psbeam.plans.characterize import characterize

##########
# Module #
##########
from .plan_stubs import prep_img_motors
from .utils.argutils import as_list, field_prepend
from .plans import walk_to_pixel, measure_average, measure

logger = logging.getLogger(__name__)

def beam_statistics(detectors, array_field="image1.array_data",
                    size_field="image1.array_size",
                    centroid_field="stats2.centroid", image_data=True,
                    ad_data=True, image_num=10, cent_num=10, image_delay=1, cent_delay=None,
                    image_filters=None, cent_filters=None, drop_missing=True,
                    filter_kernel=(9,9), resize=1.0, uint_mode="scale",
                    min_area=100, filter_factor=3, min_area_factor=3,
                    kernel=(9,9), thresh_mode="otsu", thresh_factor=3,
                    timeout=None, pim_timeout=15, **kwargs):
    """
    Calculates statistics of the beam at each of the detectors by running a
    beam-profile characterization pipeline and/or computing basic statistics of
    the stats plugin.

    Parameters
    ----------
    detectors : list of detector objs
    	List of detectors to go through and calculate the beam profile on

    array_field : str
    	The string name of the array_data signal.

    size_field : str
    	The string name of the signal that will provide the shape of the image.

    centroid_field : str
    	The string name of the signal that provides AD centroids.

    image_data : bool, optional
    	Determines whether plan should gather image statistics.

    ad_data : bool, optional
    	Determines whether plan should gather AD statistics.

    image_num : int, optional
        Number of measurements that need to pass the image filters.
    
    cent_num : int, optional
        Number of measurements that need to pass the image filters.

    image_delay : float, optional
        Minimum time between consecutive image reads of the detectors.

    cent_delay : float, optional
        Minimum time between consecutive centroid reads of the detectors.    

    image_filters : dict, optional
        Key, callable pairs of event keys and single input functions that
        evaluate to True or False, that will be passed to measure function for
    	array data.

    cent_filters : dict, optional
        Key, callable pairs of event keys and single input functions that
        evaluate to True or False, that will be passed to measure function for
    	array data.

    drop_missing : bool, optional
        Choice to include events where event keys are missing.

    filter_kernel : tuple, optional
    	Kernel to use when gaussian blurring in the contour filter.

    resize : float, optional
    	How much to resize the image by before doing any calculations.

    uint_mode : str, optional
    	Conversion mode to use when converting to uint8.

    min_area : float, optional
    	Minimum area of the otsu thresholded beam.

    filter_factor : float
    	Factor to pass to the filter mean threshold.

    min_area_factor : float
    	The amount to scale down the area for comparison with the mean threshold
    	contour area.
    
    kernel : tuple, optional
        Size of kernel to use when running the gaussian filter.    

    thresh_mode : str, optional
    	Thresholding mode to use. For extended documentation see
    	preprocessing.threshold_image. Valid modes are:
    		['mean', 'top', 'bottom', 'adaptive', 'otsu']

    thresh_factor : int or float, optional
    	Factor to pass to the mean threshold.

    timeout : None or float, optional
    	Global timeout for the statistics gathering.
        
    pim_timeout : None or float, optional
    	Timeout that gets passed to the move method of the pim object.

    Computed Statistics
    -------------------
    sum_mn_raw
    	Mean of the sum of the raw image intensities.
    
    sum_std_raw
    	Standard deviation of sum of the raw image pixel intensities.
    
    sum_mn_prep
    	Mean of the sum of the preprocessed image pixel intensities. 
    
    sum_std_prep
    	Standard deviation of the sum of the preprocessed image pixel
    	intensities.
    
    mean_mn_raw
    	Mean of the mean of the raw image pixel intensities.
    
    mean_std_raw
    	Standard deviation of the mean of the raw image pixel intensities.
    
    mean_mn_prep
    	Mean of the mean of the preprocessed image pixel intensities.
    
    mean_std_prep
    	Standard deviation of the mean of the preprocessed image pixel
    	intensities.
    
    area_mn
    	Mean of the area of the contour of the beam.
    
    area_std
    	Standard deviation of area of the contour of the beam.
    
    centroid_x_mn
    	Mean of the contour centroid x.
    
    centroid_x_std
    	Standard deviation of the contour centroid x.
    
    centroid_y_mn
    	Mean of the contour centroid y.
    
    centroid_y_std
    	Standard deviation of the contour centroid y.
    
    length_mn
    	Mean of the contour length.
    
    length_std
    	Standard deviation of the contour length.
    
    width_mn
    	Mean of the contour width.
    
    width_std
    	Standard deviation of the contour width.
    
    match_mn
    	Mean score of contour similarity to a binary image of a circle.
    
    match_std
    	Standard deviation of score of contour similarity to a binary image of
    	a circle.    

    Returns
    -------
    beam_stats : dict
    	Dictionary containing the statistics obtained for each detector.
    """
    N = len(detectors)
    beam_stats = {}

    # Listify most optional arguments
    array_field = as_list(array_field, N)
    size_field = as_list(size_field, N)
    image_num = as_list(image_num, N)
    cent_num = as_list(cent_num, N)    
    image_delay = as_list(image_delay, N, iter_to_list=False)
    cent_delay = as_list(cent_delay, N, iter_to_list=False)
    image_filters = as_list(image_filters, N)
    cent_filters = as_list(image_filters, N)
    drop_missing = as_list(drop_missing, N)
    filter_kernel = as_list(filter_kernel, N, iter_to_list=False)
    resize = as_list(resize, N)
    uint_mode = as_list(uint_mode, N)
    min_area = as_list(min_area, N)
    filter_factor = as_list(filter_factor, N)
    min_area_factor = as_list(min_area_factor, N)    
    kernel = as_list(kernel, N, iter_to_list=False)
    thresh_mode = as_list(thresh_mode, N)
    thresh_factor = as_list(thresh_factor, N)

    # Begin pipeline
    start_time = time.time()
    for idx in range(N):
        # Before each walk, check the global timeout.
        if timeout is not None and time.time() - start_time > timeout:
            raise RuntimeError("Pre-alignment stats has timed out after "
                               "{0}s".format(time.time() - start_time))
    
        logger.debug("putting imager in")
        ok = (yield from prep_img_motors(idx, detectors, timeout=pim_timeout))

        # Be loud if the yags fail to move! Operator should know!
        if not ok:
            err = "Detector motion timed out!"
            logger.error(err)
            raise RuntimeError(err)

        # Add the detectors as keys to stats with an empty dict
        beam_stats[detectors[idx].name] = {}

        # Get beam image statistics
        if image_data:            
            beam_stats[detectors[idx].name] = yield from characterize(
                detectors[idx].detector, array_field[idx], size_field[idx],
                num=image_num[idx], filters=image_filters[idx],
                delay=image_delay[idx], filter_factor=filter_factor[idx],
                drop_missing=drop_missing[idx], kernel=kernel[idx],
                uint_mode=uint_mode[idx], min_area=min_area[idx], 
                filter_kernel=filter_kernel[idx], thresh_mode=thresh_mode[idx],
                resize=resize[idx], thresh_factor=thresh_factor[idx],**kwargs)

        # Gather AD data            
        if ad_data:
            if cent_filters[idx] is None:
                cent_x, cent_y = [centroid_field + val for val in ("_x", "_y")]
                cent_filter = {
                    field_prepend(
                        cent_x, detectors[idx].detector).replace(
                            ".","_") : lambda x : x > 0,
                    field_prepend(
                        cent_y, detectors[idx].detector).replace(
                            ".","_") : lambda x : x > 0,
                }
            else:
                cent_filter = cent_filters[idx]
            
            ad_data = yield from measure([detectors[idx]], num=cent_num[idx],
                                         delay=cent_delay[idx],
                                         drop_missing=drop_missing[idx],
                                         filters=cent_filter)

            # Mean centroid position and std
            for cent in (centroid_field + "_x", centroid_field + "_y"):
                key = field_prepend(cent, detectors[idx].detector).replace(
                    ".","_")
                cent_data = [data[key] for data in ad_data]
                
                # Mean and std of the centroids
                beam_stats[detectors[idx].name]["centroid_{0}_mn_ad".format(
                    key[-1])] = np.mean(cent_data)
                beam_stats[detectors[idx].name]["centroid_{0}_std_ad".format(
                    key[-1])] = np.std(cent_data)

    return beam_stats
    
