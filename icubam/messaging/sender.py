from absl import logging

from icubam.messaging import sms_sender
from icubam.messaging.telegram import bot, integrator
from icubam.messaging import email_sender


class Sender:
  """The Sender class is responsible for sending messages to the users.

  It decides the channel to be used to contact the user: sms, email or
  via telegram bot depending on the user itself and the configuration of
  the server.
  """
  def __init__(self, config, db, queue, tg_bot=None):
    self.config = config
    self.db = db
    self.queue = queue

    self.sms_sender = None
    if self.config.TW_KEY is not None:
      self.sms_sender = sms_sender.get(config)

    self.email_sender = None
    if self.config.SMTP_HOST is not None:
      self.email_sender = email_sender.get(config)

    self.telegram_bot = None
    telegram_setup = integrator.TelegramSetup(config, db)
    if telegram_setup.is_on:
      self.telegram_bot = bot.TelegramBot(config) if tg_bot is None else tg_bot

  async def process(self):
    """Keeps reading the sending queue and does send the messages."""
    async for msg in self.queue:
      try:
        user = self.db.get_user(msg.user_id)
        await self.send(msg, user)
      except Exception as e:
        logging.warning(f'Could not send message in message loop {e}.')
      finally:
        self.queue.task_done()

  async def send(self, msg, user) -> bool:
    """Sends the message to a single user."""
    if user.telegram_chat_id is not None:
      await self.telegram_bot.send(user.telegram_chat_id, msg.html)
      return True
    elif (self.config.SMTP_HOST is not None and user.email is not None):
      self.email_sender.send(user.email, 'ICUBAM', msg.html)
      return True
    elif user.telephone is not None:
      self.sms_sender.send(msg.phone, msg.text)
      return True
    return False
