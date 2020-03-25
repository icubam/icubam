"""MessageBird SMS Object"""
import messagebird
import nexmo


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

def get_sender(config, sms_carrier=None):
  sms_carrier = sms_carrier or config.sms.carrier
  if sms_carrier.upper() == 'MB':
    return MBSender(config.MB_KEY)
  if sms_carrier.upper() == 'NX':
    return NXSender(config.NX_KEY, config.NX_API)
  else:
    raise ValueError('Incorrect value in config: {config.SENDER}.')

if __name__ == "__main__":
  from icubam import config

  ms = get_sender(sms_carrier='NX')
  ms.send_message("33698158092", "test NX")
  ms = get_sender(sms_carrier='MB')
  ms.send_message("33698158092", "test MB")
