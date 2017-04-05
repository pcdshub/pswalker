# Template for two tilted flat mirrors

from components import Imager, FlatMirror, Source

class TwoFlatTiltedMirrorsTwoImagers(object):
	def __init__(self, **kwargs):
		self.source = kwargs.get("source", Source())
		self.mirror_1 = kwargs.get("mirror_1", FlatMirror())
		self.mirror_2 = kwargs.get("mirror_2", FlatMirror())
		self.imager_1 = kwargs.get("imager_1", Imager())
		self.imager_2 = kwargs.get("imager_2", Imager())
        self.p1 = kwargs.get("p1", None)   #Desired point at imager 1
        self.p2 = kwargs.get("p2", None)   #Desired point at imager 2

    @property
    def goal_x_1(self):
        goal = self.imager_1.x + (self.p1 - self.imager_1.image_xsz/2 + 1)*self.imager_1.mppix
        return goal

    @property
    def goal_x_2(self):
        goal = self.imager_2.x + (self.p2 - self.imager_2.image_xsz/2 + 1)*self.imager_2.mppix
        return goal
