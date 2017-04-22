#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ophyd.status import wait as status_wait
# from lightpath import LightController
# TODO: When we test with a real lightpath, uncomment this and make sure
# lightpath is in the environment

_controller = None


def init_controller(controller=_controller):
    """
    Ensure we're using an initialized controller.

    Parameters
    ----------
    controller: lightpath.LightController, optional
        If None, we'll initialize the global _controller instance and return
        it. Otherwise, we'll return the argument unchanged.

    Returns
    -------
    controller: lightpath.LightController
    """
    if controller is None:
        controller = LightController()
        global _controller
        _controller = controller
    return controller


def get_path(device, exclude=None, path=None, controller=_controller):
    """
    Initialize the controller if necessary and get the path to input device.

    Parameters
    ----------
    device: object with "name" attribute and "remove" method.
        The device that the path ends in. It needs a name to be compared to the
        devices in lightpath, because there's no guarantee that lightpath's
        internal objects are the same as ours.

    exclude: list of objects with "name" attribute
        Devices to exclude from the path.

    path: lightpath.BeamPath, optional
        If provided, we'll ignore the device and controller arguments and use
        this path instead. Must be a valid argument to prune_path.

    controller: lightpath.LightController, optional
        If not provided, we'll initialize and/or use the global _controller
        object. If provided, we'll use the provided controller. If the
        controller is a fake/test object, we expect it to have a "path_to"
        method that expects the name kwarg, returning a lightpath.BeamPath
        object or stand-in that would have been a valid path parameter.

    Returns
    -------
    path: lightpath.BeamPath
        The path to our input device.
    """
    if path is None:
        controller = init_controller(controller)
        path = controller.path_to(name=device.name)
    return prune_path(path, exclude=exclude)


def prune_path(path, exclude=None):
    """
    Return a new path that is like the old path but without some devices.

    Parameters
    ----------
    path: lightpath.BeamPath
        If not a real path, it must have the "devices" attribute, where each
        device has a "name" attribute, and the __init__ must take *args where
        each argument is a device.

    exclude: list of objects with "name" attribute, optional.
        If not provided, we will not modify path. Otherwise, these objects will
        be removed from the path.

    Returns
    -------
    path: lightpath.BeamPath
        Instantied with the list of devices constructor.
    """
    if exclude is None:
        exclude = []
    if not isinstance(exclude, list):
        exclude = [exclude]
    exclude = [x.name for x in exclude]
    devices = [d for d in path.devices if d.name not in exclude]
    return path.__class__(*devices)


def clear_lightpath(device, exclude=None, wait=False, timeout=None,
                    passive=False, path=None, controller=_controller):
    """
    Clear a path to a device on the beamline.

    Parameters
    ----------
    device: object with "name" attribute
        The device that we want to bring beam to.

    exclude: list of objects with "name" attribute, optional
        Devices to exclude from the clearing step.

    wait: bool, optional
        If True, we'll wait for the path to be clear before returning.

    timeout: float, optional
        If we wait and the clear takes more than timeout seconds, return early.

    passive: bool, optional
        If True, passive devices will also be cleared.

    path: lightpath.BeamPath, optional
        If provided, we'll ignore the device and controller arguments and use
        this path instead. If it's a fake path, it needs to implement the
        "clear" method and be a viable argument to get_path. Each of the
        containing devices must include a "remove" method.

    controller: lightpath.LightController, optional
        If not provided, we'll initialize and/or use the global _controller
        object. If provided, we'll use the provided controller. If the
        controller is a fake/test object, it must be a viable argument to
        get_path.
    """
    path = get_path(device, exclude=exclude, path=path, controller=controller)
    return path.clear(wait=wait, timeout=timeout, passive=passive)
