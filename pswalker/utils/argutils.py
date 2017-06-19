#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .. import examples
from ophyd import Signal, Device


def as_list(obj, length=None, tp=None):
    """
    Force an argument to be a list, optionally of a given length, optionally
    with all elements cast to a given type if not None.
    """
    # If the obj is None, return empty list or fixed-length list of Nones
    if obj is None:
        if length is None:
            return []
        return [None] * length
    # Otherwise, attempt to cast to a list in case we have some iterable
    # Unless obj is a string, which casts to a list incorrectly
    is_list = isinstance(obj, list)
    if not is_list and not isinstance(obj, str):
        try:
            obj = list(obj)
            is_list = True
        except:
            pass
    if not is_list:
        if length is None:
            obj = [obj]
        else:
            obj = [obj] * length
    # We definitely have a list now. Cast to the type.
    # Let exceptions here bubble up to the top.
    if tp is not None:
        obj = [tp(o) for o in obj]
    return obj


def group_sorted(sort_param, *args):
    zipped = list(zip(sort_param, *args))
    zipped.sort(lambda x: x[0])
    unzip = zip(*zipped)
    return [as_list(z) for z in unzip]


def get_field(device, field):
    try:
        return device.db[field]
    except (AttributeError, KeyError):
        logger.debug("Cannot get field %s from device %s", field, device)
        return None

def field_prepend(field, obj):
    """
    Prepend the name of the Ophyd object to the field name

    Parameters
    ----------
    field : str
        Field name

    obj : object
        Object with :attr:`.name`
    
    Returns
    -------
    target_field : str
        The field maybe prepended with the object name
    """
    if isinstance(obj, (Device, examples.TestBase)) and obj.name not in field:
        field = "{}_{}".format(obj.name, field)
    elif isinstance(obj, Signal):
        field = obj.name
    
    return field
