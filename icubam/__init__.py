from importlib.metadata import version, PackageNotFoundError

try:
    # Retrieving package version at runtime
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
   pass
