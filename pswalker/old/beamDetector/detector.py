# Needs some last minute bug testing to make sure everything was ported 
# into the class correctly.

import cv2
import numpy as np
import matplotlib.pyplot as plt
# from joblib import Memory
from matplotlib.patches import Rectangle
from multiprocessing import Process
from utils.cvUtils import to_uint8

# cachedir = "cache"
# mem = Memory(cachedir=cachedir, verbose=0)

################################################################################
#                                Detector Class                                #
################################################################################

class Detector(object):
    """
    Base Detector class that will handle beam detection, returning a centroid 
    and returning a bounding box.

    Kwargs:
        resize (float): Resize factor (1.0 keeps image same size).
    	kernel (tuple): Tuple of length 2 for gaussian kernel size.
        sigma (int): Gaussian std in x and y. Set 0 to compute internally.
        threshold (float): Mult. factor for which pixels to threshold. This is 
        	calculated as mean + std * threshold.
        m_thresh_max (int): Largest acceptable zeroth moment.
        m_thresh_min (int): Smallest acceptable zeroth moment.	
    """

    def __init__(self, **kwargs):
        self.resize      = kwargs.get("resize", 1.0)
        self.kernel      = kwargs.get("kernel", (11,11))
        self.sigma       = kwargs.get("sigma", 0)
        self.max_m0      = kwargs.get("max_m0", 10e5)
        self.min_m0      = kwargs.get("min_m0", 10e1)
        self.threshold   = kwargs.get("threshold", 3.0)
        self.prep_mode   = kwargs.get("prep_mode", "clip")
        
    def preprocess(self, image):
        """Preprocess the image by resizing and running a gaussian blur. 

        Args:
            image (np.ndarray): The image to be preprocessed.
        Returns:
            np.ndarray. Preprocessed Image.
    
        Depending on the specific use case this method should be overwritten to
        use the desired preprocessing pipeline.
        """
        
        image_uint = to_uint8(image, self.prep_mode)
        image_small = cv2.resize(image_uint, (0,0), fx=self.resize, fy=self.resize)
        image_gblur = cv2.GaussianBlur(image_small, self.kernel, self.sigma)
        return image_gblur

    def get_contour(self, image):
        """Returns the first contour of the contour list.
        
        Args:
            image (np.ndarray): Image to extract the contours from.
        Returns:
            np.ndarray. First element of contours list which lists the boundaries 
            	of the contour.

        Method is making an implicit assumption that there will only be one
        contour (beam) in the image. 
        """
        _, image_thresh = cv2.threshold(
            image, image.mean() + self.threshold*image.std(), image.max(),
            cv2.THRESH_TOZERO)
        _, contours, _ = cv2.findContours(image_thresh, 1, 2)
        idx = 0
        if len(contours) > 1:
            print(len(contours))
            max_area = 0
            for i, cnt in enumerate(contours):
                _, _, w, h = self.get_bounding_box(contour=cnt)
                if w*h > max_area:
                    idx = i
                    max_area = w*h
        return contours[idx]

    def get_moments(self, image=None, contour=""):
        """Returns the moments of an image.

        Kwargs:
            image (np.ndarray): Image to calculate moments from.
            contour (np.ndarray): Beam contour boundaries.
        Returns:
            list. List of zero, first and second image moments for x and y.

        Attempts to find the moments using an inputted contours first, but if it
        isn't inputted it will compute the contours of the image then compute
        the moments.
        """
        try:
            return cv2.moments(contour)
        except TypeError:
            contour = self.get_contour(image)
            return cv2.moments(contour)

    def get_centroid(self, M):
        """Returns the centroid using the inputted image moments.

        Centroid is computed as being the first moment in x and y divided by the
        zeroth moment.

        Args:
            M (list): Moments of an image.
        Returns:
            tuple. Centroid of the image.
        """    
        return int(M['m10']/M['m00']), int(M['m01']/M['m00'])

    def get_bounding_box(self, image=None, contour=""):
        """Finds the up-right bounding box that contains the inputted contour.

        Kwargs:
            image (np.ndarray): Image to get a bounding box for.
            contour (np.ndarray): Beam contour boundaries.
        Returns:
            tuple. Contains x, y, width, height of bounding box.

        It should be noted that the x and y coordinates are for the bottom left
        corner of the bounding box. Use matplotlib.patches.Rectangle to plot.
        """
        try:
            return cv2.boundingRect(contour)
        except TypeError:
            contour = self.get_contour(image)
            return cv2.boundingRect(contour)

    def beam_is_present(self, M=None, image=None, contour=""):
        """Checks if there is a beam in the image by checking the value of the 
        zeroth moment.

        Kwargs:
            M (list): Moments of an image. 
            image (np.ndarray): Image to check beam presence for.
            contour (np.ndarray): Beam contour boundaries.

        Returns:
            bool. True if beam is present, False if not.

        TODO:
            While a lower bound makes sense, an upper bound was found to be 
            necessary as well. This should be investigated.
        """    
        try:
            return M['m00'] < self.max_m0 and M['m00'] > self.min_m0
        except (TypeError, IndexError):
            if contour:
                M = self.get_moments(contour=contour)
            else:
                image_prep = self.preprocess(image)
                contour = self.get_contour(image_prep)
                M = self.get_moments(contour=contour)
            return M['m00'] < self.max_m0 and M['m00'] > self.min_m0

    def detect(self, image):
        """Checks for beam presence and returns the centroid and bounding box 
        of the beam. Returns None if no beam is present.

        Args:
            image (np.ndarray): Image to find the beam on.
        Kwargs:
            resize (float): Resize factor (1.0 keeps image same size).
            kernel (tuple): Tuple of length 2 for gaussian kernel size.        
        Returns:
            tuple. Tuple of centroid and bounding box. None, None if no beam is
                present.
        """
        image_prep = self.preprocess(image, resize=self.resize, 
                                     kernel=self.kernel)
        contour = self.get_contour(image_prep)
        M = self.get_moments(contour=contour)
        centroid, bounding_box = None, None
        if self.beam_is_present(M):
            centroid     = [pos//self.resize for pos in self.get_centroid(M)]
            bounding_box = [val//self.resize for val in self.get_bounding_box(
                image_prep, contour)]
        return centroid, bounding_box

    def find(self, image):
        """Returns the centroid and bounding box of the beam.

        Args:
            image (np.ndarray): Image to find the beam on.
        Kwargs:
            resize (float): Resize factor (1.0 keeps image same size).
            kernel (tuple): Tuple of length 2 for gaussian kernel size.        
        Returns:
            tuple. Tuple of centroid and bounding box. None, None if no beam is
                present.
                
        This method assumes that beam is known to be present.
        """
        image_prep = self.preprocess(image)
        contour = self.get_contour(image_prep)
        M = self.get_moments(contour=contour)
        centroid     = [pos//self.resize for pos in self.get_centroid(M)]
        bounding_box = [val//self.resize for val in self.get_bounding_box(
            image_prep, contour)]
        return centroid, bounding_box

    def _plot(self, image, centroids, bounding_boxes, msg):
        """Internal method. Plots the inputted image optionally with the 
        centroid, bounding box and text.

        Args:
            image (np.ndarray): Image to plot.
            centroid (tuple): X,y coordinates of the centroid.
            bounding_box (tuple): X,y,w,h of the up-right bounding box.
            msg (str): Text to display on bottom right of image.
            
        Handles multiple centroids or bounding boxes in one image by inputting a 
        list of tuples. Allows continuation of script execution using the Process
        object.
        """
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.imshow(image)
        for centroid, bounding_box in zip(centroids, bounding_boxes):
            if isinstance(centroid, tuple) and len(centroid) == 2:
                circ = plt.Circle(centroid, radius=5, color='g')
                ax.add_patch(circ)
                if not msg:
                    msg = "Centroid: {0}".format(centroid)
            if isinstance(bounding_box, tuple) and len(tuple) == 4:
                x,y,w,h = bounding_box
                box = Rectangle((x,y),w,h,linewidth=2,edgecolor='r',
                                facecolor='none')
                ax.add_patch(box)
        if msg:
             plt.text(0.95, 0.05, msg, ha='right', va='center', color='w',
                      transform=ax.transAxes)
        plt.grid()
        plt.show()

    def plot(self, image, centroid=[], bounding_box=[], msg="", wait=False):
        """Plots the inputted image optionally with the centroid, bounding box
        and text. Can halt execution or continue.

        Args:
            image (np.ndarray): Image to plot.
        Kwargs:
            centroid (tuple): X,y coordinates of the centroid.
            bounding_box (tuple): X,y,w,h of the up-right bounding box.
            msg (str): Text to display on bottom right of image.
            wait (bool): Halt script execution until image is closed.
            
        Handles multiple centroids or bounding boxes in one image by inputting a 
        list of tuples.
        """
        if isinstance(centroid, tuple):
            centroid = [centroid]
        if isinstance(bounding_box, tuple):
            bounding_box = [bounding_box]
        if wait:
            self._plot(
                image, centroids=centroid, bounding_boxes=bounding_box, msg=msg)
        else:
            plot = Process(target=self._plot, args=(image, centroid, 
                                                    bounding_box, msg))
            plot.start()

if __name__ == "__main__":
    pass


