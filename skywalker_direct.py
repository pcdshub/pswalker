################################################################################
#                                  Skywalker                                   #
################################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import matplotlib.pyplot as plt
from psp.Pv import Pv
from joblib import Memory
from beamDetector.detector import Detector
from walker.iterwalk import IterWalker
from simtrace import run_sim

# import matlabfunc                         #function that takes all the parameters
                                          #as input then returns 3 arrays

N = 256

################################################################################
#                                Imager Class                                  #
################################################################################

class Imager(object):
    """
    Imager object that will encapsulate the various yag screens along the
    beamline.
    """

    def __init__(self, x, z, detector=Detector(mode="norm")):
        self.x = x
        self.z = z
        self.detector = detector
        self.image    = None
        self.centroid = None
        self.bounding_box = None
        self.pos = np.array([self.z, self.x])

    def get(self):
        """Get an image from the imager."""
        return self.image

    def get_centroid(self):
        """Return the centroid of the image."""
        # if self.detector.beam_is_present(self.image):
        self.centroid, self.bounding_box = self.detector.find(self.image)
        return self.centroid
        # else:
        #     raise ValueError

################################################################################
#                                 Mirror Class                                 #
################################################################################

class Mirror(object):
    """
    Mirror class to encapsulate the two HOMS (or any) mirrors.
    """

    def __init__(self, x, alpha, z):
        self.x = x
        self.alpha = alpha
        self.z = z
        self.pos = np.array([self.z, self.x])

################################################################################
#                                 Source Class                                 #
################################################################################

class Source(object):
    def __init__(self, x, xp, y, yp, z):
        self.x  = x
        self.xp = xp
        self.y  = y
        self.yp = yp
        self.z = z
        self.pos = np.array([self.z, self.x])
    
################################################################################
#                               Helper Functions                               #
################################################################################

def put_val(pv, val):
    try:
        pv.put(float(val))
    except ValueError:
        print("Invalid input type. Must be castable to float.")    

def distance(x1, x2):
    return np.linalg.norm(x2-x1)


################################################################################
#                              Simulator Functions                             #
################################################################################

def simulator(imager1, imager2, imager3, und_x, und_xp, und_y, und_yp, und_z, 
              m1h_x, m1h_alpha, m1h_z, m2h_x, m2h_alpha, m2h_z, p3h_img, p3h_z, 
              dg3_img, dg3_z, mx, my, ph_e):
    image1, image2, image3 = run_sim(mx, my, ph_e, 10, 10, und_x, und_xp, m1h_x, 
                                     m1h_alpha, m2h_x, m2h_alpha, 5, und_yp)
    imager1.image = np.array(image1).T
    imager2.image = np.array(image2).T
    imager3.image = np.array(image3).T
    # import IPython; IPython.embed()

def plot(imager1, imager2, imager3, p1, p2, centroid=True):
	fig = plt.figure()
	fig.suptitle('Beam Images', fontsize=20)
	ax = fig.add_subplot(131)
	ax.imshow(imager1.image)	
	plt.title('P2H')
	if centroid:
		circ = plt.Circle(imager1.get_centroid(), radius=5, color='g')
		ax.add_patch(circ)
		plt.text(0.95, 0.05, "Centroid: {0}".format(imager1.centroid), 
		         ha='right', va='center', color='w', transform=ax.transAxes)

	bx = fig.add_subplot(132)
	bx.imshow(imager2.image)
	plt.title('P3H')
	if centroid:
		circ = plt.Circle(imager2.get_centroid(), radius=5, color='g')
		bx.add_patch(circ)
		plt.text(0.95, 0.05, "Centroid: {0}".format(imager2.centroid), 
		         ha='right', va='center', color='w', transform=bx.transAxes)
	plt.axvline(x=p1, linestyle='--')

	cx = fig.add_subplot(133)
	cx.imshow(imager3.image)
	plt.title('DG3')
	if centroid:
		circ = plt.Circle(imager3.get_centroid(), radius=5, color='g')
		cx.add_patch(circ)
		plt.text(0.95, 0.05, "Centroid: {0}".format(imager3.centroid), 
		         ha='right', va='center', color='w', transform=cx.transAxes)
	plt.axvline(x=p2, linestyle='--')
	plt.grid()
	plt.show()

################################################################################
#                                     Main                                     #
################################################################################

if __name__ == "__main__":

    # Initial Conditions
    # Undulator Vals
    und_x = 0
    und_xp = 0
    und_y = 0
    und_yp = 0
    und_z = 0

    # M1H Vals
    m1h_x = 0
    m1h_alpha = -1e-6
    m1h_z = 90.510

    # P2H Vals
    p2h_img = 1.2332 * 0.0254
    p2h_z = 100.828
    p2h = Imager(p2h_img, p2h_z)

    # M2H Vals
    m2h_x = 0.306 * 0.0254 / 10
    # m2h_x = 0
    m2h_alpha = 0
    m2h_z = 101.843

    # P3H Vals
    p3h_img = 0
    p3h_z = 103.660

    # DG3 Vals
    dg3_img = 0
    dg3_z = 375.000

    
    # Simulation values
    mx = 601
    my = 601
    ph_e = 10000

    # Goal Pixels
    p1 = N/2
    p2 = N/2
    alpha = 0

    # Beamline Objects
    # Undulator
    undulator = Source(und_x, und_xp, und_y, und_yp, und_z)
    # M1H
    m1h = Mirror(m1h_x, m1h_alpha, m1h_z)
    # M2H
    m2h = Mirror(m2h_x, m2h_alpha, m2h_z)
    # P3H
    p3h = Imager(p3h_img, p3h_z)
    # DG3
    dg3 = Imager(dg3_img, dg3_z)

    # Alignment procedure
    walker = IterWalker(undulator, m1h, m2h, p3h, dg3, p1=p1, p2=p2)
    simulator(p2h, p3h, dg3, und_x, und_xp, und_y, und_yp, und_z, m1h_x, 
              m1h_alpha, m1h_z, m2h_x, m2h_alpha, m2h_z, p3h_img, p3h_z, 
              dg3_img, dg3_z, mx, my, ph_e)
    plot(p2h, p3h, dg3, p1, p2, centroid=True)


    try:
	    while True:
	        alpha, turn = walker.step()
	        print("\nNew alpha {0} for {1}".format(alpha, turn))
	        print("M1H: {0} M2H: {1}".format(m1h.alpha, m2h.alpha))
	        print("D1: {0} D2: {1}".format(walker._d1_x, walker._d2_x))	        
	        if turn == "alpha1":
	            m1h_alpha = alpha
	            m1h.alpha = alpha
	        elif turn == "alpha2":
	            m2h_alpha = alpha
	            m2h.alpha = alpha
	        simulator(p2h, p3h, dg3, und_x, und_xp, und_y, und_yp, und_z, 
	                  m1h_x, m1h_alpha, m1h_z, m2h_x, m2h_alpha, m2h_z, p3h_img, 
	                  p3h_z, dg3_img, dg3_z, mx, my, ph_e)
	        plot(p2h, p3h, dg3, p1, p2, centroid=True)
    except StopIteration:
        print("Reached End")

    # for i in range(2):



