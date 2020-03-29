import urllib.parse

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
    self.sender = sms_sender.get(self.config)
    self.queue = queues.Queue()
    components = urllib.parse.urlparse(self.config.server.base_url)
    self.hosts = set([components.hostname, 'localhost', "127.0.0.1"])
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
    hosts = [h.replace('.', '\.') for h in self.hosts]
    return tornado.web.Application(
      tornado.routing.HostMatches(r'({})'.format('|'.join(hosts))),
      self.routes)

  async def process(self):
    async for msg in self.queue:
      try:
        self.sender.send(msg.phone, msg.text)
      finally:
        self.queue.task_done()

  def run(self, delay=None):
    self.scheduler.schedule_all(delay)
    super().run()
