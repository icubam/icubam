from absl import logging
from tornado import queues
import tornado.routing
import tornado.web

from icubam import base_server
from icubam.messaging import sms_sender
from icubam.messaging import scheduler
from icubam.www import token


class MessageServer(base_server.BaseServer):
  """Sends and schedule SMS."""

  def __init__(self, config, port=8889):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.messaging.port
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
    self.callbacks = [self.process]

  def make_app(self):
    return tornado.web.Application(self.routes)

  async def process(self):
    async for msg in self.queue:
      try:
        self.sender.send(msg.phone, msg.text)
      finally:
        self.queue.task_done()

  def run(self, delay=None):
    self.scheduler.schedule_all(delay)
    super().run()
