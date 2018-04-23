#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from pswalker.sim.pim import PIM
from pswalker.path import prune_path, get_path, clear_lightpath


@pytest.mark.skip('deprecated')
def test_prune_path():
    i = 0
    some_devices = list()
    while i < len(lightpath.devices):
        some_devices.append(lightpath.devices[i])
        i += 2
    for d in some_devices:
        assert d in lightpath.devices, "Some error writing the test"
    new_path = prune_path(lightpath, exclude=some_devices)
    for d in some_devices:
        assert d in lightpath.devices, "Path mutated from prune_path"
    for d in some_devices:
        assert d not in new_path.devices, "Removed device still in path!"
    for d in new_path.devices:
        assert d in lightpath.devices, "New path, new objects... Wasteful."


@pytest.mark.skip('deprecated')
def test_get_path_sanity():
    new_path = get_path(None, path=lightpath)
    for d1, d2 in zip(lightpath.path, new_path.path):
        assert d1 == d2, "Path from new_path changes devices or their order"


@pytest.mark.skip('deprecated')
def test_clear_lightpath():
    for device in lightpath.devices:
        device.insert()
    clear_lightpath(None, path=lightpath, wait=True)
    assert len(lightpath.blocking_devices) == 0, \
        "Some devices not removed: {}".format(path.blocking_devices)
    for device in lightpath.devices:
        device.insert()
    exclude_device = lightpath.path[1]
    clear_lightpath(None, exclude=exclude_device, path=lightpath, wait=True)
    assert len(lightpath.blocking_devices) == 1, \
        "Only one device should be in! {}".format(lightpath.blocking_devices)
