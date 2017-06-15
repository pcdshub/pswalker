#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import random
import time
import threading

from ophyd import Signal
from ophyd.ophydobj import OphydObject
from ophyd.positioner import SoftPositioner
from bluesky.plans import sleep, checkpoint

from pswalker.examples import YAG

logger=logging.getLogger(__name__)


def collector(field, output):
    """
    Reimplement bluesky.callbacks.collector to not raise exception when field
    is missing. Instead, log a warning.
    """
    def f(name, event):
        try:
            output.append(event['data'][field])
            logger.debug("%s collector has collected, all output: %s",
                         field, output)
        except KeyError:
            logger.warning("did not find %s in event doc, skipping", field)

    return f


def plan_stash(plan, stash_queue, *args, **kwargs):
    val = yield from plan(*args, **kwargs)
    stash_queue.put(val)


def make_store_doc(dest, filter_doc_type='all'):
    def store_doc(doc_type, doc):
        if filter_doc_type == 'all' or doc_type == filter_doc_type:
            dest.append(doc)
    return store_doc


class SlowSoftPositioner(SoftPositioner):
    """
    Soft positioner that moves to the destination slowly, like a real motor
    """
    def __init__(self, *, n_steps, delay, position, **kwargs):
        super().__init__(**kwargs)
        self.n_steps = n_steps
        self.delay = delay
        self._position = position
        self._stopped = False

    def _setup_move(self, position, status):
        self._run_subs(sub_type=self.SUB_START, timestamp=time.time())

        self._started_moving = True
        self._moving = True
        self._stopped = False

        delta = (position - self.position)/self.n_steps
        pos_list = [self.position + n * delta for n in range(1, self.n_steps)]
        pos_list.append(position)

        thread = threading.Thread(target=self._move_thread,
                                  args=(pos_list, status))
        logger.debug("test motor start moving")
        thread.start()

    def stop(self, *, success=False):
        self._stopped = True
        logger.debug("stop test motor")

    def _move_thread(self, pos_list, status):
        ok = True
        for p in pos_list:
            if self._stopped:
                ok = False
                break
            if not self._stopped:
                time.sleep(self.delay)
                self._set_position(p)
        self._done_moving(success=ok)
        logger.debug("test motor done moving")


class MotorSignal(Signal):
    """
    Signal that reports its value to be that of a given positioner object
    """
    def __init__(self, motor, name=None, parent=None):
        super().__init__(name=name, parent=parent)
        motor.subscribe(self.put_cb)

    def put_cb(self, *args, value, **kwargs):
        self.put(value)


class FakePath(OphydObject):
    SUB_VALUE = "value"
    SUB_PTH_CHNG = SUB_VALUE
    _default_sub = SUB_PTH_CHNG

    def __init__(self, *devices):
        self.devices = sorted(devices, key=lambda d: d.read()[d.name + "_z"]["value"])
        super().__init__()

    def clear(self, *args, **kwargs):
        for device in self.devices:
            if device.blocking:
                device.set("OUT")

    # Looks dumb but I kind of need it because a Reader is subtly different
    # than an OphydObject
    def _run_subs(self, *args, sub_type=_default_sub, **kwargs):
        super()._run_subs(*args, sub_type=sub_type, **kwargs)

    def subscribe(self, *args, **kwargs):
        # Potential danger if we subscribe multiple times in a test
        for dev in self.devices:
            dev.subscribe(self._run_subs)
        super().subscribe(*args, **kwargs)

    @property
    def blocking_devices(self):
        return [d for d in self.devices if d.blocking]


def ruin_my_path(path):
    choices = [d for d in path.devices if isinstance(d, YAG)]
    device = random.choice(choices)
    device.set("IN")


def sleepy_scan():
    yield from checkpoint()
    yield from sleep(0.2)
