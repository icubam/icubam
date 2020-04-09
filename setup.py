from setuptools import setup

setup(
  name='icubam',
  description='ICU Bed Availability Monitor',
  license='Apache',
  packages=['icubam'],
  zip_safe=False,
  python_requires=">=3.7",
  package_data={
    # If any package contains *.txt or *.rst files, include them:
    "": ["*.env"]
  }
)
