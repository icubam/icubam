import unittest

import icubam


class PackageTestCase(unittest.TestCase):
    def test_version(self):
        self.assertHasAttr(icubam, '__version__')

