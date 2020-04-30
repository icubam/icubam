from absl import logging

from icubam.messaging import message_formatter
from icubam.messaging import sms_sender
from icubam.messaging.telegram import integrator
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
    self.formatter = message_formatter.MessageFormatter()

    try:
      self.sms_sender = sms_sender.get(config)
    except Exception as e:
      logging.warning(f"Cannot set sms_sender {e}")
      self.sms_sender = None

    try:
      self.email_sender = email_sender.get(config)
    except Exception as e:
      logging.warning(f"Cannot set email_sender {e}")
      self.email_sender = None

    # This might return be None if telegram is not properly set.
    self.telegram_bot = integrator.TelegramSetup(config, db, tg_bot=tg_bot).bot

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
    self.formatter.format(msg)
    if self.telegram_bot is not None and user.telegram_chat_id is not None:
      await self.telegram_bot.send(user.telegram_chat_id, msg.html)
      return True
    elif user.email is not None and self.email_sender is not None:
      self.email_sender.send(user.email, 'ICUBAM', msg.html)
      return True
    elif self.sms_sender is not None and user.telephone is not None:
      self.sms_sender.send(msg.phone, msg.text)
      return True
    return False
