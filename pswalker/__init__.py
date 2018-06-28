import os.path
import pcdsdevices # Pick up ophyd 1.2.0 hotfix via import
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
