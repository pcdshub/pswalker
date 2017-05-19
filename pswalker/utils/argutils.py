#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
    if isinstance(obj, str):
        obj = [obj]
    else:
        try:
            obj = list(obj)
        # If this fails, we have a single object.
        except:
            # With no length specified, just stash into a list.
            if length is None:
                obj = [obj]
            # With length specified, extend to the specified length
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


'''
    # Cause havoc if we didn't give equal length lists
    num = None
    for arg in (detectors, motors, goals):
        err = "detectors, motors, and goals must be equal length lists."
        try:
            n = len(arg)
        except:
            logger.exception(err)
            raise
        if num is None:
            num = n
        elif num != n:
            logger.error(err)
            raise TypeError(err)

    # Cause havoc if any of these aren't the right length
    for arg in (starts, first_steps, gradients, detector_fields, motor_fields,
                tolerances, averages):
        err = "If provided, each list argument must be the same length."
        if num != len(arg):
            logger.error(err)
            raise TypeError(err)

    # Sort list arguments on detector "sort" field.
    sort_parameters = [get_field(d, sort) for d in detectors]
    if all(s is not None for s in sort_parameters):
        sorts = group_sorted(sort_parameters, detectors, motors, goals, starts,
                             first_steps, gradients, detector_fields,
                             motor_fields, tolerances, averages)
        detectors = sorts[1]
        motors = sorts[2]
        goals = sorts[3]
        starts = sorts[4]
        first_steps = sorts[5]
        gradients = sorts[6]
        detector_fields = sorts[7]
        motor_fields = sorts[8]
        tolerances = sorts[9]
        averages = sorts[10]
'''
def get_field(device, field):
    try:
        return device.db[field]
    except (AttributeError, KeyError):
        logger.debug("Cannot get field %s from device %s", field, device)
        return None



