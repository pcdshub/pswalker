"""
Overrides for AreaDetector base and pcdsdevices base to be used in simulated 
devices.
"""
from collections import OrderedDict

def ad_group(cls, attr_suffix, **kwargs):
    """
    Definition creation for groups of 'empty' signals in areadetectors.
    """
    defn = OrderedDict()
    for attr in attr_suffix:
        defn[attr] = (cls, kwargs)
    return defn
