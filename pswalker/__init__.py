import logging
import os.path
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

logfile = os.path.join(os.path.dirname(__file__), "log.txt")
logging.basicConfig(level=logging.DEBUG, filename=logfile,
                    format='%(asctime)s - %(levelname)s ' +
                           '- %(name)s - %(message)s')
logger = logging.getLogger(__name__)
