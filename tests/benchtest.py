"""
Benchtest the Skywalker algorithm against the two mirror system
"""
############
# Standard #
############
import os
import sys
import logging
import argparse

###############
# Third Party #
###############
from bluesky import RunEngine
from bluesky.tests.utils import MsgCollector
from bluesky.plans import run_wrapper
from pcdsdevices.sim import pim, source, mirror


##########
# Module #
##########

def benchtest(centroid_noise = 0.,
              infinite_yag=True,
              log_level = 'INFO',
              goal1 = 210,
              goal2 = 270,
              tolerances = 5,
              average   = 1):
    """
    Parameters
    ----------
    """
    #Configure logger
    log_level = getattr(logging, log_level, None)

    #Report invalid logging level
    if not isinstance(log_level, int):
        raise ValueError("Invalid log level : {}".format(log_level))

    #Create basic configuration
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(levelname)s ' +
                               '- %(name)s - %(message)s')
    #Make sure we are using current checkout
    sys.path.insert(0,
            os.path.join(os.path.abspath(os.path.dirname(__file__)),'..'))

    from pswalker.examples  import patch_pims
    from pswalker.skywalker import skywalker

    #Instantiate simulation
    s = source.Undulator('test_undulator')
    m1 = mirror.OffsetMirror('test_m1h', 'test_m1h_xy', z=90.510, alpha=0.0014)
    m2 = mirror.OffsetMirror('test_m2h', 'test_m2h_xy', x=0.0317324, z=101.843,
                             alpha=0.0014)
    y1 = pim.PIM('test_p3h', x=0.0317324, z=103.660,
                 zero_outside_yag= not infinite_yag)
    y2 = pim.PIM('test_dg3', x=0.0317324, z=375.000,
                 zero_outside_yag= not infinite_yag)
    patch_pims([y1, y2], mirrors=[m1, m2], source=s)

    #Add noise
    y1.centroid_noise = centroid_noise
    y2.centroid_noise = centroid_noise

    #Create Skywalker plan
    plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x', 'pitch',
                     [goal1, goal2], first_steps=30, tolerances=tolerances,
                     averages=average, timeout=10)
    
    #Create RunEngine
    RE = RunEngine({})
    collector = MsgCollector()
    RE.msg_hook = collector
    RE(run_wrapper(plan))

    #Analyze Performance
    print(len(RE.msg_hook.msgs))


if __name__ == '__main__':
    #Command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--goal1', action='store',
                        dest='goal1', default=210, type=float,
                        help='Target pixel on first imager')
    parser.add_argument('--goal2', action='store',
                        dest='goal2', default=270, type=float,
                        help='Target pixel on second imager')
    parser.add_argument('--infinite', action='store', type=bool,
                        dest='infinite_yag', default=False,
                        help='Assume all yags are infinitely large')
    parser.add_argument('--noise', action='store', type=float,
                        dest='centroid_noise', default=5.0,
                        help='Noise level of centroid measurements')
    parser.add_argument('--tolerance', action='store', type=float,
                        dest='tolerances', default=2.0,
                        help='Tolerance of each target')
    parser.add_argument('--average', action='store', type=int,
                        dest='average', default=1,
                        help='Number of shots to average over')
    parser.add_argument('--log', action='store', type=str,
                        dest='log_level', default='INFO',
                        help='Target pixel on second imager')
    #Run benchtest
    benchtest(**vars(parser.parse_args()))
