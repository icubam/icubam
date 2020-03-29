from absl import logging
import tornado.ioloop
from tornado import queues
import tornado.web
from icubam.db import sqlite
from icubam.messaging import sms_sender
from icubam.messaging import scheduler
from icubam.www import token
from icubam import base_server


class MessageServer(base_server.BaseServer):
  """Sends and schedule SMS."""

  def __init__(self, config, port=None):
    port = port if port is not None else self.config.messaging.port
    super().__init__(config, port)
    self.sender = sms_sender.get(self.config)
    self.queue = queues.Queue()
    self.scheduler = scheduler.MessageScheduler(
      db=self.db,
      queue=self.queue,
      token_encoder=token.TokenEncoder(self.config),
      base_url=self.config.server.base_url,
      max_retries=self.config.scheduler.max_retries,
      reminder_delay=self.config.scheduler.reminder_delay,
      when=self.config.scheduler.ping,
    )

  async def process(self):
    async for msg in self.queue:
      try:
        self.sender.send(msg.phone, msg.text)
      finally:
        self.queue.task_done()

  def make_app(self):
    tornado.locale.load_translations('icubam/backoffice/translations')
    self.make_routes()
    return tornado.web.Application(self.routes, **settings)


  def run(self, delay=None):
    logging.info("Running {}".format(self.__class__.__name__))
    app = tornado.web.Application([])
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.spawn_callback(self.process)
    self.scheduler.schedule_all(delay)
    io_loop.start()
