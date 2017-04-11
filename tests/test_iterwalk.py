# Testing Script for iterwalk

from pswalker.iterwalk import IterWalker
from pswalker.monitor import Monitor
from pswalker.walker import Walker

def test_IterWalker_instantiates_correctly():
    monitor = Monitor()
    walker = Walker(monitor)
    assert IterWalker(walker, monitor)
