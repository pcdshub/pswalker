"""
Exceptions to be used thoughout the walker module.
"""



class WalkerException(Exception):
	"""Base walker exception class."""
	pass

class ImagerInputError(WalkerException):
	"""Incorrect inputs to Imager class."""
	pass

class MirrorInputError(WalkerException):
	"""Incorrect inputs to Mirror class."""
	pass
