from absl import logging
from typing import Dict

from icubam.messaging.telegram import bot
from icubam.www import token


class UpdateFetcher:
  """Constantly fetches updates from the telegram server.
  
  The UpdateFetcher is only used in dev mode when the webhook is not
  for convenience.
  """
  def __init__(self, config, queue, tg_bot=None):
    self.config = config
    self.queue = queue
    self.bot = bot.TelegramBot(config) if tg_bot is None else tg_bot
    self.last_update_id = 0

  async def fetch(self):
    """Fetches updates from telegram and put it to the update queue."""
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
  def __init__(self, config, db, queue, scheduler, tg_bot=None):
    self.config = config
    self.db = db
    self.queue = queue
    self.scheduler = scheduler
    self.bot = bot.TelegramBot(config) if tg_bot is None else tg_bot
    # TODO(olivier): replace with authenticator.
    self.token_encoder = token.TokenEncoder(self.config)
    admins = self.db.get_admins()
    if admins:
      self.admin_id = admins[0].user_id
    else:
      self.admin_id = self.db.add_default_admin()

  async def process(self):
    """Keep reading the update queue to deal with incoming telegram updates."""
    async for update in self.queue:
      try:
        await self.process_update(update)
      except Exception as e:
        logging.error(f'Could not process {update}: {e}')
      finally:
        self.queue.task_done()

  async def process_update(self, update: Dict):
    """Deal with a single telegram update.
    
    If the user can be authenticated and is not known as telegram user,
    register the user to our telegram message channel.

    Otherwise does nothing.
    TODO(olivier): having a responding bot would be nicer.
    """
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
        if self.scheduler is not None:
          self.scheduler.schedule(user, icu, 30)
        # TODO(olivier): i18n this.
        await self.bot.send(chatid, 'You are now registered to ICUBAM')
    else:
      print(msg)
