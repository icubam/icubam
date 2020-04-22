import tornado.routing
import tornado.web
from absl import logging  # noqa: F401
from tornado import queues

from icubam import base_server, utils
from icubam.messaging import scheduler
from icubam.messaging import sender
from icubam.messaging import telegram
from icubam.messaging.handlers import onoff, schedule


class MessageServer(base_server.BaseServer):
  """Sends and schedule SMS."""
  def __init__(self, config, port=8889):
    utils.maybe_init_sentry(config, server_name='messaging')
    super().__init__(config, port)
    self.port = port if port is not None else self.config.messaging.port
    self.db = self.db_factory.create()
    self.queue = queues.Queue()
    self.scheduler = scheduler.MessageScheduler(
      config=self.config, db=self.db, queue=self.queue
    )
    self.sender = sender.Sender(self.config, self.db, self.queue)
    self.callbacks = [self.sender.process]

    if self.config.TELEGRAM_API_KEY is not None:
      self.telegram_queue = queues.Queue()
      self.telegram_updates = telegram.UpdateProcessor(
        self.config, self.db, self.telegram_queue, self.scheduler
      )
      self.callbacks.append(self.telegram_updates.process)
      self.telegram_fetcher = telegram.TelegramFetcher(
        config, self.telegram_queue
      )
      repeat_every = self.config.messaging.telegram_updates_every * 1000
      tornado.ioloop.PeriodicCallback(
        self.telegram_fetcher.fetch, repeat_every
      ).start()

  def make_app(self):
    kwargs = dict(db_factory=self.db_factory, scheduler=self.scheduler)
    self.add_handler(onoff.OnOffHandler, **kwargs)
    self.add_handler(schedule.ScheduleHandler, **kwargs)

    # Only accepts request from same host
    return tornado.web.Application([
      (tornado.routing.HostMatches(r'(localhost|127\.0\.0\.1)'), self.routes)
    ])

  async def process(self):
    async for msg in self.queue:
      try:
        self.sender.send(msg.phone, msg.text)
      except Exception as e:
        logging.error(f'Could not send message in message loop {e}.')
      finally:
        self.queue.task_done()

  def run(self, delay=None):
    self.scheduler.schedule_all(delay)
    super().run()
