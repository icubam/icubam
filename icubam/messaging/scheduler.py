import datetime
import functools
import time
from absl import logging
import tornado.ioloop
from icubam.messaging import message
from icubam.www.handlers import update
from icubam.www import updater
from icubam import time_utils


class MessageScheduler:
  """Schedules the sending of SMS to users."""

  def __init__(self,
               config,
               db,
               queue,
               token_encoder,
               base_url: str = 'http://localhost:8888/',
               max_retries: int = 2,
               reminder_delay: int = 60*30,
               when=[(9, 30), (17, 0)]):
    self.config = config
    self.db = db
    self.token_encoder = token_encoder
    self.queue = queue
    self.base_url = base_url
    self.max_retries = max_retries
    self.reminder_delay = reminder_delay
    self.when = [time_utils.parse_hour(h) for h in when]
    self.phone_to_icu = {}
    self.messages = []
    self.timeouts = {}
    self.updater = updater.Updater(self.config, None)
    self.build_messages()

  def build_messages(self):
    """Build the messages to be sent to each user depending on its ICU."""
    users_df = self.db.get_users()
    self.messages = []
    for index, row in users_df.iterrows():
      print(row)
      url = self.updater.get_url(row.icu_id, row.icu_name)
      # TODO(olivier): fix when user-id is in
      user_id = row.telephone
      msg = message.Message(
        row.icu_id, row.icu_name, row.telephone, user_id, row.name)
      msg.build(url)
      self.messages.append(msg)

  def schedule_all(self, delay=None):
    """Schedules messages for all the users."""
    if delay is None:
      if not self.when:
        logging.warning('No ping time. Check config.')
        return

      delay = int(time_utils.get_next_timestamp(self.when) - time.time())
    for msg in self.messages:
      self.schedule(msg, delay=delay)

  def schedule(self, msg, delay=None):
    """Schedule a message for a single user."""
    if delay is None:
      if not self.when:
        logging.warning('No ping time. Check config.')
        return

      delay = int(time_utils.get_next_timestamp(self.when) - time.time())
    io_loop = tornado.ioloop.IOLoop.current()
    logging.info('Scheduling {} in {}s.'.format(msg.icu_name, delay))
    self.timeouts[msg.phone] = io_loop.call_later(delay, self.may_send, msg)

  async def may_send(self, msg):
    # This message was never sent: send it!
    if msg.first_sent is None:
      return await self.do_send(msg)

    # Otherwise check if it has been answered or sent too many times.
    df = self.db.get_bedcount()
    last_update = df[df.icu_id == msg.icu_id].update_ts
    try:
      last_update = int(last_update.iloc[0])
    except:
      last_update = None
    uptodate = (last_update is not None) and (last_update > msg.first_sent)
    # The message has been answered or too many tries, send for next session.
    if uptodate or (msg.attempts > self.max_retries):
      msg.reset()
      # This message will be sent again at the next session.
      return self.schedule(msg)
    else:
      await self.do_send(msg)

  async def do_send(self, msg):
    msg.attempts += 1
    if msg.first_sent is None:
      msg.first_sent = time.time()

    logging.info('Sending to {} now ({}/{})'.format(
      msg.icu_name, msg.attempts, self.max_retries + 1))
    if self.queue is not None:
      await self.queue.put(msg)
    self.schedule(msg, delay=self.reminder_delay)
