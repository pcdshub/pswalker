############
# Standard #
############
import logging

###############
# Third Party #
###############
import pytest
import numpy as np
from bluesky             import Msg, RunEngine
from bluesky.plans       import mv, run_wrapper

##########
# Module #
##########
from pswalker.statistics import beam_statistics

TOL = 5
logger = logging.getLogger(__name__)

tmo = 10

@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("resize", [1.0])
@pytest.mark.parametrize("kernel", [(9,9)])
@pytest.mark.parametrize("filter_kernel", [(9,9)])
@pytest.mark.parametrize("uint_mode", ["scale"])
@pytest.mark.parametrize("thresh_mode", ["otsu"])
@pytest.mark.parametrize("min_area", [100])
@pytest.mark.parametrize("num", [5])
@pytest.mark.parametrize("thresh_factor", [3])
def test_beam_statistics(RE, resize, kernel, uint_mode, thresh_mode, min_area,
                         thresh_factor, filter_kernel, num,
                         lcls_two_bounce_system):
    s, m1, m2, y1, y2 = lcls_two_bounce_system    
    array_str = "image1.array_data"
    size_str = "image1.array_size"

    def test_plan():
        plan = beam_statistics(
            [y1, y2], array_field=array_str, size_field=size_str, averages=num,
            kernel=kernel, resize=resize, uint_mode=uint_mode,
            thresh_factor=thresh_factor, filter_kernel=filter_kernel,
            thresh_mode=thresh_mode)
        stats = yield from plan
        import IPython; IPython.embed()

    
    RE(run_wrapper(test_plan()))
    
