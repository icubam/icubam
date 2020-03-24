"""MessageBird SMS Object"""
import messagebird


class MBSender:
  """Initializes and wrap a MessageBird sender object."""
  def __init__(self, api_key, originator):
    self._api_key = api_key
    self._originator = originator
    self._client = messagebird.Client(api_key)

  def send_message(self, dest, contents):
    message = self._client.message_create(
      self._originator, dest, contents, {"reference": "Foobar"}
    )
    return message
