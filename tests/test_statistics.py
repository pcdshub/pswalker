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
@pytest.mark.parametrize("ad_data", [True, False])
@pytest.mark.parametrize("image_data", [True, False])
def test_beam_statistics(RE, resize, kernel, uint_mode, thresh_mode, min_area,
                         thresh_factor, filter_kernel, num, delay, ad_data,
                         image_data, lcls_two_bounce_system):
    _, _, _, y1, y2 = lcls_two_bounce_system
    array_str = "image1.array_data"
    size_str = "image1.array_size"

    def test_plan():
        stats = yield from beam_statistics(
            [y1, y2], array_field=array_str, size_field=size_str, num=num,
            kernel=kernel, resize=resize, uint_mode=uint_mode,
            thresh_factor=thresh_factor, filter_kernel=filter_kernel,
            thresh_mode=thresh_mode, md="all", image_delay=delay,
            ad_data=ad_data, image_data=image_data)

        for _, det in stats.items():
            for key, val in det.items():
                if key == "md":
                    continue
                assert(not np.isnan(val) or not np.isinf(val) or not None)

    RE(run_wrapper(test_plan()))
    
@pytest.mark.parametrize("resize", [1.0])
@pytest.mark.parametrize("kernel", [(9,9)])
@pytest.mark.parametrize("filter_kernel", [(9,9)])
@pytest.mark.parametrize("uint_mode", ["scale"])
@pytest.mark.parametrize("thresh_mode", ["otsu"])
@pytest.mark.parametrize("min_area", [100])
@pytest.mark.parametrize("num", [5])
@pytest.mark.parametrize("thresh_factor", [3])
@pytest.mark.parametrize("delay", [0])
@pytest.mark.parametrize("ad_data", [True])
@pytest.mark.parametrize("image_data", [True])
def test_beam_statistics_raises_runtimeerror_on_timeout(
        RE, resize, kernel, uint_mode, thresh_mode, min_area, thresh_factor,
        filter_kernel, num, delay, ad_data, image_data, lcls_two_bounce_system):
    _, _, _, y1, y2 = lcls_two_bounce_system
    array_str = "image1.array_data"
    size_str = "image1.array_size"

    def test_plan():
        stats = yield from beam_statistics(
            [y1, y2], array_field=array_str, size_field=size_str, num=num,
            kernel=kernel, resize=resize, uint_mode=uint_mode,
            thresh_factor=thresh_factor, filter_kernel=filter_kernel,
            thresh_mode=thresh_mode, md="all", image_delay=delay,
            ad_data=ad_data, image_data=image_data, timeout=-1)

    with pytest.raises(RuntimeError):
        RE(run_wrapper(test_plan()))


@pytest.mark.parametrize("resize", [1.0])
@pytest.mark.parametrize("kernel", [(9,9)])
@pytest.mark.parametrize("filter_kernel", [(9,9)])
@pytest.mark.parametrize("uint_mode", ["scale"])
@pytest.mark.parametrize("thresh_mode", ["otsu"])
@pytest.mark.parametrize("min_area", [100])
@pytest.mark.parametrize("num", [5])
@pytest.mark.parametrize("thresh_factor", [3])
@pytest.mark.parametrize("delay", [0])
@pytest.mark.parametrize("ad_data", [True])
@pytest.mark.parametrize("image_data", [True])
def test_beam_statistics_raises_runtimeerror_on_stuck_motor(
        RE, resize, kernel, uint_mode, thresh_mode, min_area, thresh_factor,
        filter_kernel, num, delay, ad_data, image_data, lcls_two_bounce_system):
    _, _, _, y1, y2 = lcls_two_bounce_system
    array_str = "image1.array_data"
    size_str = "image1.array_size"

    # Set the motor set_and_wait timeout to be 1s
    y1.timeout = 1
    # Make the motor 'stuck' by it always reading back 'OUT'
    y1.states._get_readback = lambda : "OUT"

    def test_plan():
        stats = yield from beam_statistics(
            [y1, y2], array_field=array_str, size_field=size_str, num=num,
            kernel=kernel, resize=resize, uint_mode=uint_mode,
            thresh_factor=thresh_factor, filter_kernel=filter_kernel,
            thresh_mode=thresh_mode, md="all", image_delay=delay,
            ad_data=ad_data, image_data=image_data, pim_timeout=1)

    with pytest.raises(RuntimeError):
        RE(run_wrapper(test_plan()))
        
        

