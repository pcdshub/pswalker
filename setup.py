import versioneer
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
    'version':           versioneer.get_version(),
    'cmdclass':          versioneer.get_cmdclass(),
    'install_requires':  ['nose'],
    'packages':          ['beamDetector'],
    'scripts':           [],
    'name':              'psbeam'
}

setup(**config)
