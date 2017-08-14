#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .. import examples
from ophyd import Signal, Device
from collections.abc import Iterable


def as_list(obj, length=None, tp=None, iter_to_list=True):
    """
    Force an argument to be a list, optionally of a given length, optionally
    with all elements cast to a given type if not None.

    Paramters
    ---------
    obj : Object
    	The obj we want to convert to a list.

    length : int or None, optional
    	Length of new list. Applies if the inputted obj is not an iterable and
    	iter_to_list is false.

    tp : type, optional
    	Type to cast the values inside the list as.

    iter_to_list : bool, optional
    	Determines if we should cast an iterable (not str) obj as a list or to
    	enclose it in one.

    Returns
    -------
    obj : list
    	The object enclosed or cast as a list.
    """
    # If the obj is None, return empty list or fixed-length list of Nones
    if obj is None:
        if length is None:
            return []
        return [None] * length
    
    # If it is already a list do nothing
    elif isinstance(obj, list):
        pass

    # If it is an iterable (and not str), convert it to a list
    elif isiterable(obj) and iter_to_list:
        obj = list(obj)
        
    # Otherwise, just enclose in a list making it the inputted length
    else:
        try:
            obj = [obj] * length
        except TypeError:
            obj = [obj]
        
    # Cast to type; Let exceptions here bubble up to the top.
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


def isiterable(obj):
    """
    Function that determines if an object is an iterable, not including 
    str.

    Parameters
    ----------
    obj : object
        Object to test if it is an iterable.

    Returns
    -------
    bool : bool
        True if the obj is an iterable, False if not.
    """
    if isinstance(obj, str):
        return False
    else:
        return isinstance(obj, Iterable)
