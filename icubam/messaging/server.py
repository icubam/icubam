import tornado.routing
import tornado.web
from absl import logging  # noqa: F401
from tornado import queues

from icubam import base_server, sentry
from icubam.messaging import scheduler
from icubam.messaging import sender
from icubam.messaging.telegram import integrator
from icubam.messaging.handlers import onoff, schedule


class MessageServer(base_server.BaseServer):
  """Sends and schedule SMS."""
  def __init__(self, config, port=8889, telegram_setup=None):
    sentry.maybe_init_sentry(config, server_name='messaging')
    super().__init__(config, port)
    self.port = port if port is not None else self.config.messaging.port
    self.db = self.db_factory.create()
    self.queue = queues.Queue()
    self.scheduler = scheduler.MessageScheduler(
      config=self.config, db=self.db, queue=self.queue
    )
    self.sender = sender.Sender(self.config, self.db, self.queue)
    self.callbacks = [self.sender.process]

    self.telegram_setup = telegram_setup
    if self.telegram_setup is None:
      self.telegram_setup = integrator.TelegramSetup(
        self.config, self.db, self.scheduler
      )
    self.telegram_setup.setup_fetching(self.callbacks)

  def make_app(self):
    kwargs = dict(db_factory=self.db_factory, scheduler=self.scheduler)
    self.add_handler(onoff.OnOffHandler, **kwargs)
    self.add_handler(schedule.ScheduleHandler, **kwargs)
    self.add_handler(schedule.ScheduleHandler, **kwargs)

    # Only accepts request from same host
    app_routes = [
      (tornado.routing.HostMatches(r'(localhost|127\.0\.0\.1)'), self.routes)
    ]
    self.telegram_setup.add_routes(app_routes)
    return tornado.web.Application(app_routes)

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
