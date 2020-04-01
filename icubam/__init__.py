# pkg_resources is installed with setuptools
from pkg_resources import get_distribution, DistributionNotFound

try:
  __version__ = get_distribution(__name__).version
except DistributionNotFound:
  # package is not installed
  pass
