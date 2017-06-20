#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bluesky.plans import configure


def namify_config(obj, **cfg):
    """
    Prepend everything in cfg's keys with obj.name_, and remove entries where
    the value is None.
    """
    return {obj.name + "_" + k: v for k, v in cfg.items() if v is not None}


def named_configure(obj, **cfg):
    """
    Plan where we namify the config and then yield from configure.
    """
    cfg = namify_config(obj, **cfg)
    return (yield from configure(obj, **cfg))


def pim_configure(pim, event_code=140, width=300000, delay_ticks=94096,
                  polarity=1, trigger_mode=2,
                  image_mode=2):
    """
    Macro for doing standard pim configuration.
    """
    cfg = dict(detector_evr_event_code=event_code,
               detector_evr_width=width,
               detector_evr_delay_ticks=delay_ticks,
               detector_evr_polarity=polarity,
               detector_cam_trigger_mode=trigger_mode,
               detector_cam_image_mode=image_mode,
               )
    return (yield from named_configure(pim, **cfg))


def pim_lens_configure(pim, zoom=25, focus=None):
    """
    Macro for setting the zoom and focus for a pim.
    """
    cfg = dict(zoom=zoom,
               focus=focus,
               )
    return (yield from named_configure(pim, **cfg))


def pim_centroid_configure(pim, plugin=2, ndarray_port='CAM',
                           blocking_callbacks=False,
                           min_callback_time=0, compute_centroid=True,
                           centroid_threshold=512, detector_rotation=0):
    """
    Macro for configuring a pim's areadetector stats plugin to compute a
    half-maximum centroid.
    """
    cfg = dict(ndarray_port=ndarray_port,
               blocking_callbacks=blocking_callbacks,
               min_callback_time=min_callback_time,
               compute_centroid=compute_centroid,
               centroid_threshold=centroid_threshold,
               rotation=detector_rotation,
               )
    cfg = {'detector_stats{}_{}'.format(plugin, k): v for k, v in cfg.items()}
    return (yield from named_configure(pim, **cfg))
