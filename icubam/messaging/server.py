from absl import logging
import tornado.ioloop
from tornado import queues
import tornado.web
from icubam.db import sqlite
from icubam.messaging import sms_sender
from icubam.messaging import scheduler


class MessageServer:
  """Sends and schedule SMS."""

  def __init__(self, config, port=8889):
    self.config = config
    self.db = sqlite.SQLiteDB(self.config.db.sqlite_path)
    self.port = port
    self.sender = sms_sender.get_sender(self.config.sms.carrier)
    self.queue = queues.Queue()
    self.scheduler = scheduler.MessageScheduler(
      base_url=self.config.server.base_url
      db=self.db,
      queue=self.queue,
    )

  async def process(self):
    async for msg in self.queue:
      try:
        self.sender.send_message(msg.phone, msg.text)
      finally:
        self.queue.task_done()

  def run(self):
    logging.info("Running {}".format(self.__class__.__name__))
    app = tornado.web.Application([])
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.spawn_callback(self.process)
    self.scheduler.schedule_all()
    io_loop.start()
