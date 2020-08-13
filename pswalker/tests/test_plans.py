############
# Standard #
############
import logging

###############
# Third Party #
###############
import lmfit
import pytest
import numpy as np
from ophyd.sim import SynSignal, SynAxis, motor, det
from bluesky.preprocessors import run_wrapper

##########
# Module #
##########
from pswalker.plans import measure, measure_average, measure_centroid
from pswalker.plans import walk_to_pixel, fitwalk
from pswalker.callbacks import LiveBuild, LinearFit
from pswalker.utils.exceptions import FilterCountError
from .utils import collector

logger = logging.getLogger(__name__)


class ParabolicFit(LiveBuild):
    def __init__(self, y, x, average=1):
        def parabola(x, a0):
            return a0*(x**2)

        model = lmfit.Model(parabola,
                            independent_vars=['x'],
                            missing='drop')

        super().__init__(model, y, independent_vars={'x': x},
                         init_guess={'a0': 1}, update_every=1,
                         average=average)

    def eval(self, x=0., **kwargs):
        # Check result
        super().eval(x)

        # Structure input and add past result
        kwargs = {'x': np.asarray(x)}
        kwargs.update(self.result.values)

        # Return prediction
        return self.result.model.eval(**kwargs)

    def backsolve(self, target, **kwargs):
        # Make sure we have a fit
        super().backsolve(target, **kwargs)
        # Gather line information
        a0 = self.result.values['a0']
        # Return x position
        return {'x': np.sqrt(target/a0)}


def test_measure_average(RE, one_bounce_system):
    logger.debug("test_measure_average")
    _, mot, det = one_bounce_system

    centroids = []
    readbacks = []
    col_c = collector(det.name + '_detector_stats2_centroid_x', centroids)
    col_r = collector(mot.name + '_sim_alpha',    readbacks)

    RE(run_wrapper(measure_average([det, mot], delay=0.1, num=5)),
       {'event': [col_c, col_r]})

    assert centroids == [250., 250., 250., 250., 250.]
    assert readbacks == [0., 0., 0., 0., 0.]

    centroids.clear()
    readbacks.clear()

    # Run with array of delays
    RE(run_wrapper(measure_average([det, mot], delay=[0.1], num=2)),
       {'event': [col_c, col_r]})

    assert centroids == [250., 250.]
    assert readbacks == [0., 0.]

    # Invalid delay settings
    with pytest.raises(ValueError):
        RE(run_wrapper(measure_average([det, mot], delay=[0.1], num=3)))


def test_measure_average_system(RE, lcls_two_bounce_system):
    logger.debug("test_measure_average_system")
    _, m1, m2, y1, y2 = lcls_two_bounce_system

    centroids = []
    readbacks = []
    col_c = collector(y1.name + '_detector_stats2_centroid_x', centroids)
    col_r = collector(m1.name + '_sim_alpha',    readbacks)

    RE(run_wrapper(measure_average([y1, m1, y2, m2],
                                   delay=0.1, num=5)),
       {'event': [col_c, col_r]})

    assert centroids == [y1.detector._get_readback_centroid_x()] * 5
    assert readbacks == [m1.position] * 5

    # RE.msg_hook is a message collector
    m1_reads = 0
    m2_reads = 0
    y1_reads = 0
    y2_reads = 0
    saves = 0
    for msg in RE.msg_hook.msgs:
        if msg.command == 'read':
            if msg.obj == m1:
                m1_reads += 1
            if msg.obj == m2:
                m2_reads += 1
            if msg.obj == y1:
                y1_reads += 1
            if msg.obj == y2:
                y2_reads += 1
        if msg.command == 'save':
            saves += 1
    assert saves > 0
    assert all(map(lambda x: x == saves,
                   [m1_reads, m2_reads, y1_reads, y2_reads]))


def test_measure_centroid(RE, one_bounce_system):
    logger.debug("test_measure_centroid")

    _, mot, det = one_bounce_system
    centroids = []
    key_ext = 'detector_stats2_centroid_x'
    col_c = collector(det.name + "_" + key_ext, centroids)

    RE(run_wrapper(measure_centroid(det, average=5,
                                    target_field=key_ext)),
       {'event': [col_c]})
    assert centroids == [250., 250., 250., 250., 250.]


def test_walk_to_pixel(RE, one_bounce_system):
    logger.debug("test_walk_to_pixel")
    _, mot, det = one_bounce_system

    ##########################
    # Test on simple devices #
    ##########################
    simple_motor = SynAxis(name='motor')
    simple_det = SynSignal(name='det',
                           func=lambda: 5*simple_motor.read()['motor']['value']
                                + 2)

    # Naive step
    plan = run_wrapper(walk_to_pixel(simple_det, simple_motor, 200, 0,
                                     first_step=1e-6,
                                     tolerance=10, average=None,
                                     target_fields=['det', 'motor'],
                                     max_steps=3))
    RE(plan)
    assert np.isclose(simple_det.read()['det']['value'], 200, atol=1)

    simple_motor.set(0.)

    # Gradient
    simple_motor = SynAxis(name='motor')
    simple_det = SynSignal(name='det',
                           func=lambda: 5*simple_motor.read()['motor']['value']
                                + 2)
    plan = run_wrapper(walk_to_pixel(simple_det, simple_motor, 200, 0,
                                     gradient=1.6842e+06,
                                     tolerance=10, average=None,
                                     target_fields=['det', 'motor'],
                                     max_steps=3))
    RE(plan)
    assert np.isclose(simple_det.read()['det']['value'], 200, atol=1)

    ##########################
    # Test on full model #
    ##########################
    # Naive step
    cent = 'detector_stats2_centroid_x'
    plan = run_wrapper(walk_to_pixel(det, mot, 200, 0, first_step=1e-6,
                                     tolerance=10, average=None,
                                     target_fields=[cent, 'sim_alpha'],
                                     max_steps=3))
    RE(plan)
    assert np.isclose(det.read()[det.name + "_" + cent]['value'], 200, atol=1)

    mot.set(0.)

    # Gradient
    plan = run_wrapper(walk_to_pixel(det, mot, 200, 0, gradient=1.6842e+06,
                                     tolerance=10, average=None,
                                     target_fields=[cent, 'sim_alpha'],
                                     max_steps=3))
    RE(plan)
    assert np.isclose(det.read()[det.name + "_" + cent]['value'], 200, atol=10)


def test_measure(RE):
    # Simplest implementation
    plan = run_wrapper(measure([det, motor], num=5, delay=0.01))

    # Fake callback storage
    shots = list()
    cb = collector('det', shots)

    # Run simple
    RE(plan, {'event': cb})
    assert shots == [1.0, 1.0, 1.0, 1.0, 1.0]

    # Create counting detector
    index = -1

    def count():
        nonlocal index
        index += 1
        return index

    counter = SynSignal(name='intensity',
                        func=count)

    # Filtered implementation
    plan = run_wrapper(measure([counter],
                       filters={'intensity': lambda x: x > 2},
                       num=5))
    # Fake callback storage
    shots = list()
    cb = collector('intensity', shots)

    # Run filtered
    RE(plan, {'event': cb})
    assert shots == [1, 2, 3, 4, 5, 6, 7]

    # Make sure an exception is raised when we fail too many filter checks
    plan = run_wrapper(measure([counter],
                       filters={'intensity': lambda x: False},
                       num=500))
    with pytest.raises(FilterCountError):
        RE(plan)


def test_fitwalk(RE):
    # Create simulated devices
    motor = SynAxis(name='motor')
    det = SynSignal(name='centroid',
                    func=lambda: 5*motor.read()['motor']['value'] + 2)

    linear = LinearFit('centroid', 'motor', average=1)
    parabola = ParabolicFit('centroid', 'motor', average=1)
    walk = fitwalk([det], motor, [parabola, linear], 89.4,
                   average=1, tolerance=0.5)
    RE(run_wrapper(walk))

    assert np.isclose(det.read()['centroid']['value'], 89.4, 0.5)
