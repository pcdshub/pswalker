import numpy as np
import autoFocus.focus as af
import cv2
from tests.focus_tests import *
from pprint import pprint
image = cv2.imread("tests/test_yag_images_01/image01.jpg", cv2.IMREAD_GRAYSCALE)

# const = 2
# mot = VirtualMotorTest(image)
# cam = VirtualCameraTest(mot, const=const)
# pos = (-19, 19, 2)
# focus = af.Focus(motor_pv=mot, camera_pv=cam, positions=pos, method="scan")
# # ipdb.set_trace()
# a = focus.focus()
# pprint(focus._focuses)

const = 0
mot = VirtualMotorTest(image)
mot.mv(.01)
cam = VirtualCameraTest(mot, const=const, mode="hillclimb")
focus = af.Focus(motor_pv=mot, camera_pv=cam, positions=None, 
                 method="hillclimb")
#import ipdb; ipdb.set_trace()

methods = ["Powell", "CG", "L-BFGS-B", "trust-ncg", "dogleg", "COBYLA", "TNC" "BFGS", "Nelder-Mead"]
methods_scalar = ["Brent", "Bounded", "Golden"]

for method in methods:
	try:
		res = focus.focus(hc_method="brent")
		print(method, res.x)
	except:
		print("Failed for {0}".format(method))

# res = focus.focus(hc_method="brent")
# print(res)
# # print("brent", res.x)



