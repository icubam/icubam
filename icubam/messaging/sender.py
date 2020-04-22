from absl import logging

from icubam.messaging import sms_sender
from icubam.messaging import telegram
from icubam.messaging import email_sender


class Sender:
  def __init__(self, config, queue):
    self.config = config
    self.queue = queue
    self.sms_sender = sms_sender.get(config)
    self.bot = telegram.TelegramBot(config)
    self.email_sender = email_sender.SMTPEmailSender(config)

  async def process(self):
    async for msg in self.queue:
      try:
        user = self.db.get_user(msg.user_id)
        await self.send(msg, user)
      except Exception as e:
        logging.warning(f'Could not send message in message loop {e}.')
      finally:
        self.queue.task_done()

  async def send(self, msg, user):
    # TODO(olivier): make html messages for email and bot.
    if user.telegram_chat_id is not None:
      return await self.bot.send(user.telegram_chat_id, msg.txt)

    if (self.config.SMTP_HOST is not None and user.email is not None):
      self.email_sender.send(user.email, 'ICUBAM', msg.text)
    else:
      self.sms_sender.send(msg.phone, msg.text)
