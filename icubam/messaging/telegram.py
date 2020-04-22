from absl import logging
import json
import tornado.httpclient
from typing import Optional

from icubam.www import token


class TelegramBot:
  """A class to send and receive messages to/from telegram."""

  API_URL = "https://api.telegram.org/bot"
  URL = "http://telegram.me/"
  START = "/start"

  def __init__(self, config):
    self.config = config
    self.api_url = self.API_URL + self.config.TELEGRAM_API_KEY
    self.public_url = self.URL + self.config.messaging.telegram_bot
    self.client = tornado.httpclient.AsyncHTTPClient()

  async def getUpdates(self, min_id=0):
    """Returns the updates."""
    url = f"{self.api_url}/getUpdates"
    resp = await self.client.fetch(url)
    if resp.code != 200:
      logging.warning(f"Cannot fetch {url}")
      return

    try:
      data = json.loads(resp.body.decode())
    except Exception as e:
      logging.warning(f"Cannot decode json {e}")
      return

    return [u for u in data["result"] if u["update_id"] >= min_id]

  def invite_url(self, token: str) -> str:
    """Builds an invite url that send directly the user to the right place."""
    return self.public_url + self.START + token

  def extract_token(self, text: str) -> Optional[str]:
    if text.startswith(self.START):
      return text[len(self.START) + 1:]
    return None

  async def send(self, chatid: str, text: str) -> bool:
    """Sends a text to a chat."""
    request = tornado.httpclient.HTTPRequest(
      url=f"{self.api_url}/sendMessage",
      method='POST',
      headers={'Content-Type': 'application/json'},
      body=json.dumps({
        'chat_id': chatid,
        'text': text,
        'parse_mode': 'HTML',
      }),
    )
    resp = await self.client.fetch(request)
    return resp.code == 200


class TelegramFetcher:
  """Constantly fetches updates from the telegram server.
  
  Should be replaced by a webhook (but convenient for debug).
  """
  def __init__(self, config, queue):
    self.config = config
    self.queue = queue
    self.bot = TelegramBot(config)
    self.last_update_id = 0

  async def fetch(self):
    updates = await self.bot.getUpdates(min_id=self.last_update_id)
    if not updates:
      return

    last_id = updates[-1]['update_id']
    if last_id > self.last_update_id:
      self.last_update_id = last_id

    for update in updates:
      await self.queue.put(update)


class UpdateProcessor:
  """What to do when receiving an update from telegram ?

  As of today, if it is the first time we see this user, and it comes with
  the proper token, then we register it and update the scheduler about it.
  Otherwise we simply do nothing.
  """
  def __init__(self, config, db, queue, scheduler):
    self.config = config
    self.db = db
    self.queue = queue
    self.scheduler = scheduler
    self.bot = TelegramBot(config)
    self.token_encoder = token.TokenEncoder(self.config)
    admins = self.db.get_admins()
    if admins:
      self.admin_id = admins[0].user_id
    else:
      self.admin_id = self.db.add_default_admin()

  async def process(self):
    async for update in self.queue:
      try:
        await self.process_update(update)
      except Exception as e:
        logging.error(f'Could not process {update}: {e}')
      finally:
        self.queue.task_done()

  async def process_update(self, update):
    msg = update.get('message', None)
    if msg is None:
      logging.warning('Update has no message')
      return

    chatid = msg.get('chat', {}).get('id', None)
    if chatid is None:
      logging.warning('Update has no proper chat id')
      return

    # This is a start message with a token
    jwt = self.bot.extract_token(msg.get('text', ''))
    if jwt is not None:
      user, icu = self.token_encoder.authenticate(jwt, self.db)
      if user is None or icu is None:
        logging.warning('cannot identify user')
        return await self.bot.send(chatid, "Cannot identify user.")

      if user.telegram_chat_id is None:
        self.db.update_user(
          self.admin_id, user.user_id, {"telegram_chat_id": chatid}
        )
        self.scheduler.scheduler(user, icu, 30)
        # TODO(olivier): i18n this.
        await self.bot.send(chatid, 'You are now registered to ICUBAM')
    else:
      print(msg)