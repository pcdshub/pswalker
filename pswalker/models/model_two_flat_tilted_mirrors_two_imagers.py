# Template for two tilted flat mirrors

from components import Imager, FlatMirror, Source

class TwoFlatTiltedMirrorsTwoImagers(object):
	def __init__(self, **kwargs):
		self.source = kwargs.get("source", Source())
		self.mirror_1 = kwargs.get("mirror_1", FlatMirror())
		self.mirror_2 = kwargs.get("mirror_2", FlatMirror())
		self.imager_1 = kwargs.get("imager_1", Imager())
		self.imager_2 = kwargs.get("imager_2", Imager())
