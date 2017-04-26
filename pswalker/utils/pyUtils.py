# General helper functions that don't fall into a particular category

from collections.abc import Iterable

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

def isnumber(obj):
	"""
    Checks if the input is a number.

    Parameters
    ----------
    obj : object
        Object to test if it is an number.

    Returns
    -------
    bool : bool
    	True if the obj is a number, False if not.    
    """
	if isinstance(obj, str):
		try:
			float(obj)
			return True
		except ValueError:
			return False
	elif isinstance(obj, float) or isinstance(obj, int):
		return True
	else:
		return False

def _flatten(inp_iter):
	"""
    Recursively iterate through values in nested iterables.

    Parameters
    ----------
    inp_iter : iterable
        The iterable to flatten.

    Returns
    -------
    value : object
    	The contents of the iterable
    """
	for val in inp_iter:
		if isiterable(val):
			for ival in _flatten(val):
				yield ival
		else:
			yield val

def flatten(inp_iter):
	"""
    Returns a flattened list of the inputted iterator.

    Parameters
    ----------
    inp_iter : iterable
        The iterable to flatten.

    Returns
    -------
    flattened_iter : list
    	The contents of the iterable as a flat list
    """
	return list(_flatten(inp_iter))

def isempty(inp_iter):
	"""
    Checks if an iterable (nested or not) is empty.

    Parameters
    ----------
    inp_iter : iterable
        The iterable to check for emptiness.

    Returns
    -------
    bool : bool:
    	True if the iterator empty, False if not.
    """
	return not any(1 for _ in _flatten(inp_iter))
