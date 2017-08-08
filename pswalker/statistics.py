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
                    size_field="image1.array_size", num=10, timeout=None,
                    drop_missing=True, kernel=(9,9), resize=1.0,
                    uint_mode="scale", min_area=100, thresh_factor=3,
                    filter_kernel=(9,9), thresh_mode="otsu", filters=None,
                    image_delay=1, cent_delay=None, md=None, ad_data=True,
                    centroid_field="stats2.centroid", image_data=True,
                    pim_timeout=15, **kwargs):
    """
    Obtains statistics of the beam by walking the beam to the center of the
    imager, gathering shots and then returns the computed stats.
    """
    N = len(detectors)
    beam_stats = {}

    # Listify most optional arguments
    array_field = as_list(array_field, N)
    size_field = as_list(size_field, N)
    num = as_list(num, N)
    drop_missing = as_list(drop_missing, N)
    kernel = as_list(kernel, N, iter_to_list=False)
    resize = as_list(resize, N)
    uint_mode = as_list(uint_mode, N)
    min_area = as_list(min_area, N)
    thresh_factor = as_list(thresh_factor, N)
    filter_kernel = as_list(filter_kernel, N, iter_to_list=False)
    thresh_mode = as_list(thresh_mode, N)
    filters = as_list(filters, N)
    image_delay = as_list(image_delay, N, iter_to_list=False)
    cent_delay = as_list(cent_delay, N, iter_to_list=False)
    md = as_list(md, N)
    
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
                num=num[idx], filters=filters[idx], delay=image_delay[idx], 
                drop_missing=drop_missing[idx], kernel=kernel[idx],
                uint_mode=uint_mode[idx], min_area=min_area[idx], md=md[idx], 
                filter_kernel=filter_kernel[idx], thresh_mode=thresh_mode[idx],
                resize=resize[idx], thresh_factor=thresh_factor[idx],**kwargs)

        # Gather AD data            
        if ad_data:
            ad_data = yield from measure([detectors[idx]], num=num[idx],
                                         delay=cent_delay[idx],
                                         drop_missing=drop_missing[idx])

            # Mean centroid position and std
            for cent in (centroid_field + "_x", centroid_field + "_y"):
                key = field_prepend(cent,detectors[idx].detector).replace(
                    ".","_")
                cent_data = [data[key] for data in ad_data]
                
                # Mean and std of the centroids
                beam_stats[detectors[idx].name]["centroid_{0}_mn_ad".format(
                    key[-1])] = np.mean(cent_data)
                beam_stats[detectors[idx].name]["centroid_{0}_std_ad".format(
                    key[-1])] = np.std(cent_data)

    return beam_stats
    
