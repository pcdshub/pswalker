# Testing script for (ophyd) devices built in components.py

from pswalker.components import Imager, FlatMirror, Linac

################################################################################
#                                 Imager Tests                                 #
################################################################################

def test_Imager_instantiates_correctly():
    assert Imager()

################################################################################
#                               FlatMirror Tests                               #
################################################################################

def test_FlatMirror_instantiates_correctly():
    assert FlatMirror()

################################################################################
#                                 Linac Tests                                  #
################################################################################

def test_Linac_instantiates_correctly():
    assert Linac()
