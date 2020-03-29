import pkg_resources
from os import path
from setuptools.config import read_configuration

def _extract_version(package_name):
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        _conf = read_configuration(path.join(
            path.dirname(path.dirname(__file__)), 'setup.cfg')
        )
        return _conf['metadata']['version']

__version__ = _extract_version('icubam')