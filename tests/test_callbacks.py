import logging

import numpy as np
import pandas as pd
from ophyd.sim import SynSignal, SynAxis
from bluesky import RunEngine
from bluesky.plans import outer_product_scan, scan

from pswalker.callbacks import (rank_models, apply_filters, LinearFit,
                                MultiPitchFit)

logger = logging.getLogger(__name__)


def test_linear_fit():
    RE = RunEngine()

    # Expected values of fit
    expected = {'slope': 5, 'intercept': 2}

    motor = SynAxis(name='motor')
    det = SynSignal(name='centroid',
                    func=lambda: 5*motor.read()['motor']['value'] + 2)

    # Assemble fitting callback
    cb = LinearFit('centroid', 'motor',
                   update_every=None)

    RE(scan([det], motor, -1, 1, 50), cb)

    # Check accuracy of fit
    for k, v in expected.items():
        assert np.allclose(cb.result.values[k], v, atol=1e-6)

    # Check we create an accurate estimate
    assert np.allclose(cb.eval(x=10), 52, atol=1e-5)
    assert np.allclose(cb.eval(motor=10), 52, atol=1e-5)
    assert np.allclose(cb.backsolve(52)['x'], 10, atol=1e-5)


def test_multi_fit():
    RE = RunEngine()

    # Expected values of fit
    expected = {'x0': 5, 'x1': 4, 'x2': 3}

    m1 = SynAxis(name='m1')
    m2 = SynAxis(name='m2')
    det = SynSignal(name='centroid',
                    func=lambda: 5
                         + 4*m1.read()['m1']['value']
                         + 3*m2.read()['m2']['value'])

    # Assemble fitting callback
    cb = MultiPitchFit('centroid', ('m1', 'm2'),
                       update_every=None)

    RE(outer_product_scan([det], m1, -1, 1, 10, m2, -1, 1, 10, False), cb)

    # Check accuracy of fit
    logger.debug(cb.result.fit_report())
    for k, v in expected.items():
        assert np.allclose(cb.result.values[k], v, atol=1e-6)

    # Check we create an accurate estimate
    assert np.allclose(cb.eval(a0=5, a1=10), 55, atol=1e-5)
    assert np.allclose(cb.backsolve(55, a1=10)['a0'], 5, atol=1e-5)
    assert np.allclose(cb.backsolve(55, a0=5)['a1'], 10, atol=1e-5)


def test_apply_filters_handles_all_data_types():
    mock_doc = {"str": "string",  "int": 0, "float": 3.14159, "bool": True,
                "ndarray": np.arange(10), "list": list(range(10)),
                "dataframe": pd.DataFrame(np.arange(10))}

    assert not apply_filters(mock_doc, filters={"str": lambda x: False})
    assert not apply_filters(mock_doc, filters={"int": lambda x: False})
    assert not apply_filters(mock_doc, filters={"float": lambda x: False})
    assert not apply_filters(mock_doc, filters={"bool": lambda x: False})
    assert not apply_filters(mock_doc, filters={"ndarray": lambda x: False})
    assert not apply_filters(mock_doc, filters={"list": lambda x: False})
    assert not apply_filters(mock_doc, filters={"dataframe": lambda x: False})


def test_apply_filters_correctness():
    mock_doc = {'a': 4, 'b': -1}

    # Passing filters
    assert apply_filters(mock_doc, filters={'a': lambda x: x > 0})

    # Block non-zero
    assert not apply_filters(mock_doc,  filters={'b': lambda x: x > 0})

    # Exclude missing
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Exclude NaN
    mock_doc['c'] = np.nan
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Exclude NaN in array
    mock_doc['c'] = np.ones((10)) * np.nan
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Exclude NaN in string
    mock_doc['c'] = "nan"
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Exclude Inf
    mock_doc['c'] = np.inf
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Exclude Inf in array
    mock_doc['c'] = np.ones((10)) * np.inf
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Exclude Inf in string
    mock_doc['c'] = "inf"
    assert not apply_filters(mock_doc, filters={'c': lambda x: True})

    # Include missing
    assert apply_filters(mock_doc, filters={'c': lambda x: True},
                         drop_missing=False)


def test_rank_models():
    RE = RunEngine()

    # Create accurate fit
    motor = SynAxis(name='motor')
    det = SynSignal(name='centroid',
                    func=lambda: 5*motor.read()['motor']['value'] + 2)
    fit1 = LinearFit('centroid', 'motor',
                     update_every=None, name='Accurate')
    RE(scan([det], motor, -1, 1, 50), fit1)

    # Create inaccurate fit
    det2 = SynSignal(name='centroid',
                     func=lambda: 25*motor.read()['motor']['value'] + 2)
    fit2 = LinearFit('centroid', 'motor',
                     update_every=None, name='Inaccurate')
    RE(scan([det2], motor, -1, 1, 50), fit2)

    # Create inaccurate fit
    det3 = SynSignal(name='centroid',
                     func=lambda: 12*motor.read()['motor']['value'] + 2)
    fit3 = LinearFit('centroid', 'motor',
                     update_every=None, name='Midly Inaccurate')
    RE(scan([det3], motor, -1, 1, 50), fit3)

    # Rank models
    ranking = rank_models([fit2, fit1, fit3], target=22, x=4)
    assert ranking[0] == fit1
    assert ranking[1] == fit3
    assert ranking[2] == fit2
