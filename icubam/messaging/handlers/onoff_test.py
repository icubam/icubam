import unittest
from icubam.messaging.handlers import onoff

class OnOffRequestTestCase(unittest.TestCase):

  def test_silence_request(self):
    userid = 123
    icuid = 773
    on = False
    delay = 34

    request = onoff.OnOffRequest(
      user_id=userid, icu_id=icuid, on=on, delay=delay)
    encoded = request.to_json()
    self.assertIsInstance(encoded, str)

    decoded = onoff.OnOffRequest()
    self.assertEqual(decoded.user_id, None)

    decoded.from_json(encoded)
    self.assertEqual(decoded.user_id, userid)
    self.assertEqual(decoded.icu_id, icuid)
    self.assertEqual(decoded.on, on)
    self.assertEqual(decoded.on, on)
    self.assertEqual(decoded.delay, delay)
