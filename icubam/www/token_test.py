import unittest
from icubam.www import token


class TokenTest(unittest.TestCase):

  def test_encode(self):
    userid = 1234
    encoded = token.encode(userid)
    self.assertIsInstance(encoded, str)
    self.assertEqual(token.decode(encoded), userid)
