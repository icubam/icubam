import unittest
from icubam.messaging.handlers import onoff

class OnOffRequestTestCase(unittest.TestCase):

  def test_silence_request(self):
    userid = 123
    icuids = [773, 32]
    on = False
    delay = None

    request = onoff.OnOffRequest(
      user_id=userid, icu_ids=icuids, on=on, delay=delay)
    encoded = request.to_json()
    self.assertIsInstance(encoded, str)

    decoded = onoff.OnOffRequest()
    self.assertEqual(decoded.user_id, None)

    decoded.from_json(encoded)
    self.assertEqual(decoded.user_id, userid)
    self.assertEqual(len(decoded.icu_ids), len(icuids))
    self.assertEqual(decoded.icu_ids[0], icuids[0])
    self.assertEqual(decoded.on, on)
    self.assertEqual(decoded.on, on)
    self.assertEqual(decoded.delay, delay)
