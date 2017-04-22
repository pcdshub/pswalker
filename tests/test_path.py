#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pswalker.examples import YAG
from pswalker.path import prune_path, get_path, clear_lightpath


def test_valid_fake_path(fake_path_two_bounce):
    """
    Make sure that the fake path contains all methods that we need. This does
    not guarantee that the methods will work.
    """
    path = fake_path_two_bounce
    err = "Expected {}.{}"
    for attr in ("devices", "clear", "blocking_devices", "subscribe",
                 "SUB_PTH_CHNG"):
        assert hasattr(path, attr), err.format(path, attr)
    assert isinstance(path.devices, list), "Expected path.devices to be a list"
    for device in path.devices:
        for attr in ("blocking", "set", "read"):
            assert hasattr(device, attr), err.format(device, attr)


def test_prune_path(fake_path_two_bounce):
    path = fake_path_two_bounce
    some_devices = []
    i = 0
    while i < len(path.devices):
        some_devices.append(path.devices[i])
        i += 2
    for d in some_devices:
        assert d in path.devices, "Some error writing the test"
    new_path = prune_path(path, exclude=some_devices)
    for d in some_devices:
        assert d in path.devices, "Path mutated from prune_path"
    for d in some_devices:
        assert d not in new_path.devices, "Removed device still in path!"
    for d in new_path.devices:
        assert d in path.devices, "New path, new objects... Wasteful."


def test_get_path_sanity(fake_path_two_bounce):
    new_path = get_path(None, path=fake_path_two_bounce)
    for d1, d2 in zip(fake_path_two_bounce.devices, new_path.devices):
        assert d1 == d2, "Path from new_path changes devices or their order"


def test_clear_lightpath(fake_path_two_bounce):
    path = fake_path_two_bounce
    for device in path.devices:
        device.set("IN")
    clear_lightpath(None, path=path, wait=True)
    assert len(path.blocking_devices) == 0, \
        "Some devices not removed: {}".format(path.blocking_devices)
    for device in path.devices:
        device.set("IN")
    for device in path.devices:
        if isinstance(device, YAG):
            exclude_device = device
            break
    clear_lightpath(None, exclude=exclude_device, path=path, wait=True)
    assert len(path.blocking_devices) == 1, \
        "Only one device should be in! {}".format(path.blocking_devices)
