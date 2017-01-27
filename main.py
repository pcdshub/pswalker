import numpy as np
import autoFocus.focus as af
import cv2
from tests.focus_tests import *
import ipdb

image = cv2.imread("tests/test_yag_images_01/image01.jpg", cv2.IMREAD_GRAYSCALE)
const = 2
mot = VirtualMotorTest(image)
cam = VirtualCameraTest(mot, const=const)
pos = (-19, 19, 2)

focus = af.Focus(motor_pv=mot, camera_pv=cam, positions=pos, method="hillclimb")

ipdb.set_trace()

a = focus.focus()
