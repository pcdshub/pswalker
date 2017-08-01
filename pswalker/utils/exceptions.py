# Exceptions to be used throughout Walker sytem

class PSWalkerException(Exception):
	"""Base exception class for the whole module."""
	pass

################################################################################
#                              Walker Exceptions                               #
################################################################################

class WalkerException(PSWalkerException):
	"""Base walker exception class."""
	pass

class ImagerInputError(WalkerException):
	"""Incorrect inputs to Imager class."""
	pass

class MirrorInputError(WalkerException):
	"""Incorrect inputs to Mirror class."""
	pass

################################################################################
#                              Component Exceptions                            #
################################################################################

class ComponentException(PSWalkerException):
	"""Base component exception class."""
	pass

################################################################################
#                             Plan Exceptions                                  #
################################################################################
class BeamNotFoundError(PSWalkerException):
    """Fiduicial Exception"""
    pass
################################################################################
#                             ModelWalk Exceptions                             #
################################################################################

class ModelWalkException(PSWalkerException):
	"""Base ModelWalk exception class."""
	pass


################################################################################
#                              IterWalk Exceptions                             #
################################################################################

class IterWalkException(PSWalkerException):
	"""Base IterWalk exception class."""
	pass

################################################################################
#                                CNC Exceptions                                #
################################################################################

class CNCException(PSWalkerException):
	"""Base CNC exception class."""
	pass

################################################################################
#                             ModelBuild Exceptions                            #
################################################################################

class ModelBuildException(PSWalkerException):
	"""Base ModelBuild exception class."""
	pass

################################################################################
#                               Monitor Exceptions                             #
################################################################################

class MonitorException(PSWalkerException):
	"""Base ModelBuild exception class."""
	pass

################################################################################
#                               Monitor Exceptions                             #
################################################################################

class MeasureException(PSWalkerException):
    """Base Measure exception class."""
    pass

class FilterCountError(MeasureException):
    """Exception to be raised when too many events are filtered."""
    pass
