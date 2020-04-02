import unittest

from icubam.messaging import sms_sender
from icubam import config


class SmsSenderTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml', mode='dev')

  def test_from_string(self):
    self.assertIsInstance(
      sms_sender.get(self.config, 'MB'), sms_sender.MBSender)
    self.assertIsInstance(
      sms_sender.get(self.config, 'NX'), sms_sender.NXSender)
    self.assertIsInstance(
      sms_sender.get(self.config, 'nx'), sms_sender.NXSender)
    self.assertIsInstance(
      sms_sender.get(self.config, 'Fake'), sms_sender.FakeSender)
    self.assertIsInstance(
      sms_sender.get(self.config, 'fake'), sms_sender.FakeSender)
    with self.assertRaises(ValueError):
      sms_sender.get(self.config, 'dummy_sms_sender_name')


  def test_from_config(self):
    self.assertIsInstance(sms_sender.get(self.config), sms_sender.FakeSender)

  def test_send_from_fake_sender(self):
    ms = sms_sender.get(self.config, 'Fake')
    ms.send("Fake phone number", "Hello from tests")
