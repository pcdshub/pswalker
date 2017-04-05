# Exceptions to be used throughout Walker sytem

class PSWalkException(Exception):
	"""Base exception class for the whole module."""
	pass

################################################################################
#                              Walker Exceptions                               #
################################################################################

class WalkerException(PSWalkException):
	"""Base walker exception class."""
	pass

class ImagerInputError(WalkerException):
	"""Incorrect inputs to Imager class."""
	pass

class MirrorInputError(WalkerException):
	"""Incorrect inputs to Mirror class."""
	pass

################################################################################
#                            ModelWalker Exceptions                            #
################################################################################

class ModelWalkerException(PSWalkException):
	"""Base ModelWalker exception class."""
	pass

