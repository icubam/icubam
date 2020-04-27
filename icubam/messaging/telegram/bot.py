from absl import logging
import json
import os.path
import tornado.httpclient
from typing import Dict, List, Optional

from icubam.messaging.telegram import webhook


class TelegramBot:
  """A class to send and receive messages to/from telegram."""

  API_URL = "https://api.telegram.org/bot"
  URL = "http://telegram.me/"
  START = "/start"

  def __init__(self, config, client=None):
    self.config = config
    self.client = None
    self.api_url = self.API_URL + self.config.TELEGRAM_API_KEY
    self.public_url = self.URL + self.config.messaging.telegram_bot
    self.client = client
    if self.client is None:
      self.client = tornado.httpclient.AsyncHTTPClient()

  async def get(self, route: str) -> Optional[tornado.httpclient.HTTPResponse]:
    """Sends a GET request to telegram."""
    request = tornado.httpclient.HTTPRequest(
      url=f"{self.api_url}/{route}",
      method='GET',
    )
    try:
      return await self.client.fetch(request)
    except Exception as e:
      logging.warning(f'Cannot fetch telegram GET route {route}: {e}')
      return None

  async def post(self, data: Dict,
                 route: str) -> Optional[tornado.httpclient.HTTPResponse]:
    """Sends a post request to a given telegram route."""
    request = tornado.httpclient.HTTPRequest(
      url=f"{self.api_url}/{route}",
      method='POST',
      headers={'Content-Type': 'application/json'},
      body=json.dumps(data),
    )
    try:
      return await self.client.fetch(request)
    except Exception as e:
      logging.warning(f'Cannot fetch telegram POST route {route}: {e}')
      return None

  async def getUpdates(self, min_id: int = 0) -> Optional[List[Dict]]:
    """Returns the updates."""
    route = "getUpdates"
    resp = await self.get(route)
    if resp is None or resp.code != 200:
      logging.warning(f"Cannot fetch {route} from telegram.")
      return None

    try:
      data = json.loads(resp.body.decode())
    except Exception as e:
      logging.warning(f"Cannot decode json {e}")
      return None

    return [u for u in data["result"] if u["update_id"] > min_id]

  def invite_url(self, token: str) -> str:
    """Builds an invite url that send directly the user to the right place."""
    return self.public_url + self.START + token

  def extract_token(self, text: str) -> Optional[str]:
    """Extracts the token from a messages.
    
    It should be sent in a start command.
    """
    if text.startswith(self.START):
      return text[len(self.START) + 1:]
    return None

  async def send(self, chatid: str, text: str) -> bool:
    """Sends a text to a chat."""
    data = {
      'chat_id': chatid,
      'text': text,
      'parse_mode': 'HTML',
    }
    resp = await self.post(data, 'sendMessage')
    return resp is not None and resp.code == 200

  async def setWebhook(self) -> bool:
    """Sets up a webhook to receive update directly from the server."""
    url = os.path.join(
      self.config.server.base_url, webhook.TelegramWebhook.ROUTE
    )
    resp = await self.post({'url': url}, 'setWebhook')
    return resp is not None and resp.code == 200
