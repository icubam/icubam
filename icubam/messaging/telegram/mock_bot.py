import io
import json
import tornado.httpclient
from icubam.messaging.telegram import bot


class MockHTTPClient:
  """A mock http client."""
  def __init__(self, code=200):
    self.requests = []
    self.code = code
    self.body = None

  def set_body(self, data):
    if data is None:
      self.body = None
    else:
      self.body = io.BytesIO()
      self.body.write(json.dumps(data).encode())

  async def fetch(self, request):
    self.requests.append(request)
    return tornado.httpclient.HTTPResponse(
      request, code=self.code, buffer=self.body
    )


class MockTelegramBot(bot.TelegramBot):
  def __init__(self, config):
    config.TELEGRAM_API_KEY = 'key'
    config.messaging.telegram_bot = 'michel'
    config.messaging.telegram_updates_every = '60'
    super().__init__(config, MockHTTPClient())
