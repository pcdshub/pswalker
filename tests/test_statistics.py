############
# Standard #
############
import logging

###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky.plans import run_wrapper

##########
# Module #
##########
from pswalker.statistics import beam_statistics

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("resize", [1.0])
@pytest.mark.parametrize("kernel", [(9,9)])
@pytest.mark.parametrize("filter_kernel", [(9,9)])
@pytest.mark.parametrize("uint_mode", ["scale"])
@pytest.mark.parametrize("thresh_mode", ["otsu"])
@pytest.mark.parametrize("min_area", [100])
@pytest.mark.parametrize("num", [5])
@pytest.mark.parametrize("thresh_factor", [3])
@pytest.mark.parametrize("delay", [0])
def test_beam_statistics(RE, resize, kernel, uint_mode, thresh_mode, min_area,
                         thresh_factor, filter_kernel, num, delay,
                         lcls_two_bounce_system):
    _, _, _, y1, y2 = lcls_two_bounce_system
    array_str = "image1.array_data"
    size_str = "image1.array_size"

    def test_plan():
        stats = yield from beam_statistics(
            [y1, y2], array_field=array_str, size_field=size_str, num=num,
            kernel=kernel, resize=resize, uint_mode=uint_mode,
            thresh_factor=thresh_factor, filter_kernel=filter_kernel,
            thresh_mode=thresh_mode, md="all", image_delay=delay)

        for _, det in stats.items():
            for key, val in det.items():
                if key == "md":
                    continue
                assert(not np.isnan(val) or not np.isinf(val) or not None)


        import IPython; IPython.embed()

    RE(run_wrapper(test_plan()))
    
