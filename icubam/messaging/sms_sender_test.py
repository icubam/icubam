import pytest

from icubam.messaging import sms_sender
from icubam import config


@pytest.fixture()
def get_config():
  return config.Config('resources/test.toml', mode='dev')


def test_from_string(get_config):
  assert isinstance(sms_sender.get(get_config, 'MB'), sms_sender.MBSender)
  assert isinstance(sms_sender.get(get_config, 'NX'), sms_sender.NXSender)
  assert isinstance(sms_sender.get(get_config, 'nx'), sms_sender.NXSender)
  assert isinstance(sms_sender.get(get_config, 'Fake'), sms_sender.FakeSender)
  assert isinstance(sms_sender.get(get_config, 'fake'), sms_sender.FakeSender)
  with pytest.raises(ValueError, match='Incorrect sms carrier'):
    sms_sender.get(get_config, 'dummy_sms_sender_name')


def test_from_config(get_config):
  assert isinstance(sms_sender.get(get_config), sms_sender.FakeSender)


def test_send_from_fake_sender(get_config):
  ms = sms_sender.get(get_config, 'Fake')
  # send message with Fake sender is safe.
  # It only prints to standard output the message
  ms.send("Fake phone number", "Hello from tests")
