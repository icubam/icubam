from setuptools import setup

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
