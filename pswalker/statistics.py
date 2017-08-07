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
from psbeam.plans.characterize import (characterize, signal_tuple)
from bluesky.plans import checkpoint
from .utils.argutils import as_list, field_prepend

##########
# Module #
##########
from .plans import walk_to_pixel, measure_average
from .plan_stubs import prep_img_motors
from .utils.argutils import as_list, field_prepend
from .utils.exceptions import RecoverDone

logger = logging.getLogger(__name__)

def beam_statistics(detectors, array_field="image1.array_data",
                    size_field="image1.array_size", averages=10, timeout=None,
                    drop_missing=True, kernel=(9,9), resize=1.0,
                    uint_mode="scale", min_area=100, thresh_factor=3,
                    filter_kernel=(9,9), thresh_mode="otsu", filters=None,
                    **kwargs):
    """
    Obtains statistics of the beam by walking the beam to the center of the
    imager, gathering shots and then returns the computed stats.
    """
    num = len(detectors)
    beam_stats = {}

    for index in range(num):
        # Before each walk, check the global timeout.
        if timeout is not None and time.time() - start_time > timeout:
            raise RuntimeError("Pre-alignment stats has timed out after "
                               "{0}s".format(time.time() - start_time))

        logger.debug("putting imager in")
        ok = (yield from prep_img_motors(index, detectors, timeout=15))

        # Be loud if the yags fail to move! Operator should know!
        if not ok:
            err = "Detector motion timed out!"
            logger.error(err)
            raise RuntimeError(err)
        
        beam_stats[detectors[index].name] = yield from characterize(
            detectors[index].detector, array_field, size_field,
            num=averages, filters=filters, delay=1, drop_missing=drop_missing,
            kernel=kernel, resize=resize, uint_mode=uint_mode,
            min_area=min_area, thresh_factor=thresh_factor,
            filter_kernel=filter_kernel, thresh_mode=thresh_mode, **kwargs)

    return beam_stats
    
