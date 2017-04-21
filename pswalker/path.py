#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ophyd.status import wait as status_wait
from lightpath import LightController

_controller = None


def init_controller(controller=_controller):
    if controller is None:
        controller = LightController()
        global _controller
        _controller = controller
    return controller


def get_path(device, controller=_controller):
    controller = init_controller(controller)
    path = controller.path_to(name=device.name)
    return path


def prune_path(path, exclude=None):
    if not exclude:
        return
    exclude = [x.name for x in exclude]
    for name, dev in list(zip(path.device_names, path.devices)):
        if name in exclude:
            path.devices.pop(dev)


def clear_lightpath(device, exclude=None, controller=_controller, wait=False,
                    timeout=None, passive=False, ignore=None):
    path = get_path(device, controller=controller)
    prune_path(path, exclude=exclude)
    return path.clear(wait=wait, timeout=timeout, passive=passive,
                      ignore=ignore)
