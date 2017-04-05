# Components to be used in each model

################################################################################
#                                 Imager Class                                 #
################################################################################

class Imager(object):
	def __init__(self, **kwargs):
		self.x = kwargs.get("x", None)
        self.z = kwargs.get("z", None)
        self.image_xsz = 0
        self.image_ysz = 0
        self.mppix = kwargs.get("mppix", 1.25e-5)


################################################################################
#                               Flat Mirror Class                              #
################################################################################

class FlatMirror(object):
	def __init__(self, **kwargs):
		self.x = kwargs.get("x", None)
        self.z = kwargs.get("z", None)
        self.alpha = kwargs.get("alpha", None)
		

################################################################################
#                                 Source Class                                 #
################################################################################

class Source(object):
    def __init__(self, **kwargs):
		self.x = kwargs.get("x", None)
		self.y = kwargs.get("y", None)
        self.z = kwargs.get("z", None)
        self.xp = kwargs.get("xp", None)
        self.yp = kwargs.get("yp", None)
