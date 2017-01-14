
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description':       '',
    'author':            'apra (Abdullah P Rashed Ahmed)',
    'url':               '',
    'download_url':      '',
    'author_email':      'apra@slac.stanford.edu',
    'version':           '0.1',
    'install_requires':  ['nose'],
    'packages':          ['beamDetector'],
    'scripts':           [],
    'name':              'psbeam'
}

setup(**config)
