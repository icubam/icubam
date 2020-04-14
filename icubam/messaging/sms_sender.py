"""SMS Sender Abstraction"""
import abc
import inspect
import sys

from absl import logging
import messagebird
import nexmo
from twilio.rest import Client as TWCLient


class Sender(abc.ABC):
  """Base class for senders."""
  def __init__(self, config):
    self.config = config
    self._originator = self.config.sms.origin

  @abc.abstractmethod
  def send(self, dest, contents):
    return


class FakeSender(Sender):
  """Just log the message but does nothing real."""
  def send(self, dest, contents):
    destination = "+{}".format(dest.strip('+'))
    logging.info(f'Sending {contents} to {destination}.')


class MBSender(Sender):
  """Initializes and wrap a MessageBird sender object."""
  def __init__(self, config):
    super().__init__(config)
    self._api_key = self.config.MB_KEY
    self._client = messagebird.Client(self._api_key)

  def send(self, dest, contents):
    message = self._client.message_create(
      self._originator, dest.strip("+"), contents, {"reference": "Foobar"}
    )
    return message


class NXSender(Sender):
  def __init__(self, config):
    super().__init__(config)
    self._client = nexmo.Client(
      key=self.config.NX_KEY, secret=self.config.NX_API
    )

  def send(self, dest, contents):
    return self._client.send_message({
      "from": self._originator,
      "to": dest.strip("+"),
      "text": contents
    })


class TWSender(Sender):
  def __init__(self, config):
    super().__init__(config)
    self._client = TWCLient(self.config.TW_KEY, self.config.TW_API)

  def send(self, dest, contents):
    destination = "+{}".format(dest.strip('+'))
    self._client.messages.create(
      to=destination, from_=self._originator, body=contents
    )


def get(config, sms_carrier=None):
  """Returns the sender based on the name of the sms_carrier.

  Here the name of the carrier should match the name of the sender object,
  that is if the sender object is 'XXSender' the carrier name should be 'XX'
  """
  sms_carrier = sms_carrier or config.sms.carrier
  "{}Sender".format(sms_carrier)
  obj = None
  for key, member in inspect.getmembers(sys.modules[__name__]):
    if key.upper() == "{}Sender".format(sms_carrier).upper():
      obj = member
      break
  if obj is not None:
    return obj(config)
  else:
    raise ValueError(f'Incorrect sms carrier: {sms_carrier}.')
