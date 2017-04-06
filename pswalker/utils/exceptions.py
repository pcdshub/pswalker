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
#                             ModelWalk Exceptions                             #
################################################################################

class ModelWalkException(PSWalkException):
	"""Base ModelWalk exception class."""
	pass


################################################################################
#                              IterWalk Exceptions                             #
################################################################################

class IterWalkException(PSWalkException):
	"""Base IterWalk exception class."""
	pass

################################################################################
#                                CNC Exceptions                                #
################################################################################

class CNCException(PSWalkException):
	"""Base CNC exception class."""
	pass

################################################################################
#                             ModelBuild Exceptions                            #
################################################################################

class ModelBuildException(PSWalkException):
	"""Base ModelBuild exception class."""
	pass

################################################################################
#                               Monitor Exceptions                             #
################################################################################

class MonitorException(PSWalkException):
	"""Base ModelBuild exception class."""
	pass

