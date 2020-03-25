import datetime
import functools
import time
from absl import logging
import tornado.ioloop
from icubam.messaging import message
from icubam.www.handlers import update


class MessageScheduler:
  """Schedules the sending of SMS to users."""

  MESSAGE_TEMPLATE = (
    "Bonjour {},\nvoici le lien à suivre pour mettre à jour les données covid"
    " de {} sur ICUBAM: {}")

  def __init__(self,
               db,
               queue,
               token_encoder,
               base_url: str = 'http://localhost:8888/',
               max_retries: int = 2,
               reminder_delay: int = 60*30,
               when=[(9, 30), (17, 0)]):
    self.db = db
    self.token_encoder = token_encoder
    self.queue = queue
    self.base_url = base_url
    self.max_retries = max_retries
    self.reminder_delay = reminder_delay
    self.when = when
    self.phone_to_icu = {}
    self.messages = []
    self.urls = []  # for debug only
    self.timeouts = {}
    self.build_messages()

  def build_messages(self):
    """Build the messages to be sent to each user depending on its ICU."""
    users_df = self.db.get_users()
    self.messages = []
    for index, row in users_df.iterrows():
      url = "{}{}?id={}".format(
        self.base_url,
        update.UpdateHandler.ROUTE.strip('/'),
        self.token_encoder.encode_icu(row.icu_id, row.icu_name))
      text = self.MESSAGE_TEMPLATE.format(row['name'], row['icu_name'], url)
      self.urls.append(url)
      self.messages.append(
        message.Message(text, row.telephone, row.icu_id, row.icu_name))

  def get_next_moment(self, ts=None):
    """Gets the timestamp of the next moment of sending messages."""
    ts = int(time.time()) if ts is None else ts
    now = datetime.datetime.fromtimestamp(ts)
    today_fn = functools.partial(
      datetime.datetime, year=now.year, month=now.month, day=now.day)
    next = None
    sorted_moments = sorted(self.when)
    for hm in sorted_moments:
      curr = today_fn(hour=hm[0], minute=hm[1])
      if curr > now:
        next = curr
        break
    if next is None:
      hm = sorted_moments[0]
      next = today_fn(hour=hm[0], minute=hm[1]) + datetime.timedelta(1)
    return next.timestamp()

  def schedule_all(self):
    """Schedules messages for all the users."""
    delay = int(self.get_next_moment() - time.time())
    for msg in self.messages:
      self.schedule(msg, delay=delay)

  def schedule(self, msg, delay=None):
    """Schedule a message for a single user."""
    if delay is None:
      delay = int(self.get_next_moment() - time.time())
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
