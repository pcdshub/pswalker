# Testing suite for walker

from pswalker.walker import Walker
from pswalker.monitor import Monitor

def test_Walker_instantiates_correctly():
    assert Walker(Monitor())
