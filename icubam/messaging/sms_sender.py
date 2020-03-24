"""MessageBird SMS Object"""
import messagebird
import nexmo

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


class TWSender:
  def __init__(self, key, secret, originator="ICUBAM"):
    self._originator = originator
    self._client = nexmo.Client(key=key, secret=secret)

  def send_message(self, dest, contents):
    return self._client.send_message(
      {"from": self._originator, "to": dest, "text": contents}
    )

def get_sender(sms_carrier=None):
  sms_carrier = sms_carrier or config.SMS_CARRIER
  if sms_carrier == 'MB':
    return MBSender(config.MB_KEY)
  if sms_carrier == 'TW':
    return TWSender(config.TW_KEY, config.TW_API)
  else:
    raise ValueError('Incorrect value in config: {config.SENDER}.')

if __name__ == "__main__":
  from icubam import config

  ms = get_sender(sms_carrier='TW')
  ms.send_message("33698158092", "test TW")
  ms = get_sender(sms_carrier='MB')
  ms.send_message("33698158092", "test MB")
