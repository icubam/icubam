from absl import logging  # noqa: F401
from tornado import queues
import tornado.routing
import tornado.web

from icubam import base_server
from icubam.messaging import sms_sender
from icubam.messaging import scheduler


class MessageServer(base_server.BaseServer):
  """Sends and schedule SMS."""

  def __init__(self, config, port=8889):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.messaging.port
    self.sender = sms_sender.get(self.config)
    self.queue = queues.Queue()
    self.scheduler = scheduler.MessageScheduler(
      config=self.config, db=self.db, queue=self.queue)
    print([m.text for m in self.scheduler.messages])
    self.callbacks = [self.process]

  def make_app(self):
    return tornado.web.Application(self.routes)

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
