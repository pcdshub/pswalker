# Testing Script for modelbuild

from pswalker.modelbuild import ModelBuilder
from pswalker.monitor import Monitor

def test_ModelBuilder_instantiates_correctly():
    assert ModelBuilder(Monitor())
