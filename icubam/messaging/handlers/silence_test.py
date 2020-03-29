import unittest
from icubam.messaging.handlers import silence

class SilenceRequestTestCase(unittest.TestCase):

  def test_silence_request(self):
    userid = 123
    request = silence.SilenceRequest(user_id=userid)
    encoded = request.to_json()
    self.assertIsInstance(encoded, str)

    decoded = silence.SilenceRequest()
    self.assertEqual(decoded.user_id, None)
    decoded.from_json(encoded)
    self.assertEqual(decoded.user_id, userid)
