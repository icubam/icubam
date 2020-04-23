from absl import logging
import json
import tornado.web


class TelegramWebhook(tornado.web.RequestHandler):
  """Receives updates from the telegram server directly."""

  ROUTE = '/telegram'

  # Telegram hosts. See this link for more details.
  # https://core.telegram.org/bots/webhooks#testing-your-bot-with-updates
  HOSTS = r'(149\.154\.160\.0|91\.108\.4\.0)'

  def __init__(self, queue):
    self.queue = queue

  async def post(self):
    """Updates are sent JSON serialized one at a time via POST request."""
    try:
      update = json.loads(self.request.body.decode())
    except Exception as e:
      logging.warning(f'Cannot decode body from request {e}')
      self.set_status(400)
      return

    await self.queue.put(update)
