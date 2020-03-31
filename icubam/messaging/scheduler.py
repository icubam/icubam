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
    # Keys: by (user_id, icu_id)
    # Values: Tuple(timeout handle, timestamp)
    self.timeouts = {}
    self.updater = updater.Updater(self.config, None)
    self.build_messages()

  def build_messages(self):
    """Build the messages to be sent to each user depending on its ICU."""
    users = self.db.get_users()
    self.messages = []
    for user in users:
      for icu in user.icus:
        url = self.updater.get_url(icu.icu_id, icu.name)
        msg = message.Message(
          icu.icu_id, icu.name, user.telephone, user.user_id, user.name)
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
      self.schedule_message(msg, delay=delay)

  def computes_delay(self, delay=None) -> int:
    """Computes the delay if None."""
    if delay is not None:
      return int(delay)

    if not self.when:
      # TODO(olivier): double check what happens with negative delays
      logging.warning('No ping time. Check config.')
      return -1

    return int(time_utils.get_next_timestamp(self.when) - time.time())

  def schedule_message(self, msg, delay=None):
    """Schedule a message for a single user."""
    # TODO(olivier): change this when user_id is in
    key = msg.phone

    delay = self.computes_delay(delay)
    io_loop = tornado.ioloop.IOLoop.current()

    when = delay + time.time()
    timeout_when = self.timeouts.get(key, None)

    if timeout_when is None:
      self.timeouts[key] = (io_loop.call_later(delay, self.may_send, msg), when)
      logging.info('Scheduling {} in {}s.'.format(msg.icu_name, delay))
    elif when < timeout_when[1]:
      self.unschedule(msg.user_id, msg.icu_id)
      self.timeouts[key] = (io_loop.call_later(delay, self.may_send, msg), when)
      logging.info('Scheduling {} in {}s.'.format(msg.icu_name, delay))
    else:
      logging.info(f'A message is schedule before {when}, Skipping scheduling.')

  def schedule(self, user_id: int, icu_id: int, delay: Optional[int] = None):
    user = self.db.get_user(user_id)
    if user is None:
      return logging.error(f"Unknown user {user_id}")

    icus = {icu.icu_id: icu for icu in users.icus}
    if not user.is_active or icu_id not in icus:
      logging.info(f"User {user_id} from ICU {icu_id} cannot receive messages.")
      return

    url = self.updater.get_url(row.icu_id, row.icu_name)
    user_id = row.telephone
    msg = message.Message(
      row['icu_id'], row['icu_name'], row['telephone'], user_id, row['name'])
    msg.build(url)
    self.

  def unschedule(self, user_id: int, icu_id: int):
    timeout = self.timeouts.pop((user_id, icu_id), None)
    if timeout is None:
      logging.info(f'No timeout for user {user_id}')
      return

    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.remove_timeout(timeout)
    logging.info(f'Unscheduling message for {user_id} in {icu_id}.')

  def on_off(self, user_id: int, icu_id: int, on: bool, delay):
    """Switching the user on and off."""
    if not on:
      self.unschedule(user_id, icu_id)
    elif (user_id, icu_id) in self.timeouts:
      logging.info('')

  async def may_send(self, msg):
    # This message was never sent: send it!
    if msg.first_sent is None:
      return await self.do_send(msg)

    # Otherwise check if it has been answered or sent too many times.
    bed_count = self.db.get_bed_count_for_icu(msg.icu_id)
    last_update = None if bed_count is None else bed_count.last_modified
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
