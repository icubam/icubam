"""SMS Sender Abstraction"""
import messagebird
import nexmo
from twilio.rest import Client as TWCLient

from icubam import config

class MBSender:
  """Initializes and wrap a MessageBird sender object."""

  def __init__(self, api_key, originator="ICUBAM"):
    self._api_key = api_key
    self._originator = originator
    self._client = messagebird.Client(api_key)

  def send_message(self, dest, contents):
    message = self._client.message_create(
      self._originator, dest, contents, {"reference": "Foobar"}
    )
    return message


class NXSender:
  def __init__(self, key, secret, originator="ICUBAM"):
    self._originator = originator
    self._client = nexmo.Client(key=key, secret=secret)

  def send_message(self, dest, contents):
    return self._client.send_message(
      {"from": self._originator, "to": dest, "text": contents}
    )


class TWSender:
  def __init__(self, key, secret, originator="ICUBAM"):
    self._originator = originator
    # import ipdb; ipdb.set_trace()
    self._client = TWCLient(key, secret)

  def send_message(self, dest, contents):
    self._client.messages.create(to=f"+{dest}", from_=self._originator, body=contents)



def get_sender(config, sms_carrier=None):
  sms_carrier = sms_carrier or config.sms.carrier
  if sms_carrier.upper() == 'MB':
    return MBSender(config.MB_KEY)
  if sms_carrier.upper() == 'NX':
    return NXSender(config.NX_KEY, config.NX_API)
  if sms_carrier.upper() == 'TW':
    return TWSender(config.TW_KEY, config.TW_API)
  else:
    raise ValueError('Incorrect sms carrier: {sms_carrier}.')
