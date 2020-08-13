############
# Standard #
############
import logging

###############
# Third Party #
###############
from jinja2 import Environment
from bluesky.preprocessors import run_wrapper
##########
# Module #
##########
from pswalker.watcher import report_tpl, RunSummary, Watcher
from pswalker.skywalker import skywalker

def test_watcher_report_smoke(RE, lcls_two_bounce_system):
    w = Watcher()
    #Configure RE
    RE.msg_hook = w
    RE.subscribe(w, 'all')
    RE.record_interruptions = True
    #Run skywalker
    s, m1, m2, y1, y2 = lcls_two_bounce_system
    goals = [150, 150]
    #This should use homs_skywalker, but not obvious how to run that on
    #simulation system, so instead we spoof the metadata
    plan = skywalker([y1, y2], [m1, m2], 'detector_stats2_centroid_x',
                     'sim_alpha',
                     goals, first_steps=40.0, tolerances=2,
                     averages=1, timeout=10, sim=True)
    try:
        RE(plan)
    except:
        # We're not testing skywalker, we're testing the report...
        pass
    #Report
    w.report()
