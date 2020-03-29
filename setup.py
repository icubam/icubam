from setuptools import setup

NAME = "icubam"
DESCRIPTION = "ICU Bed Activity Monitor."
URL = "https://github.com/icubam/icubam"
EMAIL = "pbalapra@anl.gov"
AUTHOR = "Prasanna Balaprakash"
REQUIRES_PYTHON = ">=3.6.0"
VERSION = None

setup(name='icubam',
      version='0.1',
      description='ICU Bed Availability Monitor',
      license='Apache',
      packages=['icubam'],
      zip_safe=False,
      package_data={
        # If any package contains *.txt or *.rst files, include them:
        "": ["*.env"]
        }
      )
