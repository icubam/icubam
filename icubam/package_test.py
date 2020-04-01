import unittest

import icubam


class PackageTestCase(unittest.TestCase):
  def test_version(self):
      try:
          icubam.__version__
      except Exception:
          raise AssertionError
