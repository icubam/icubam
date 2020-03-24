from absl import logging
import tornado.ioloop
from tornado import queues
import tornado.web
from icubam.db import sqlite
from icubam.messaging import mb_sender
from icubam.messaging import scheduler
from icubam import config


class MessageServer:
  """Sends and schedule SMS."""

  def __init__(self, db_path, port=8889):
    self.db = sqlite.SQLiteDB(db_path)
    self.port = port
    self.sender = mb_sender.MBSender(config.SMS_KEY, config.SMS_ORIG)
    self.queue = queues.Queue()
    self.scheduler = scheduler.MessageScheduler(db=self.db, queue=self.queue)

  async def process(self):
    async for msg in self.queue:
      try:
        self.sender.send_message(msg.phone, msg.text)
      finally:
        self.queue.task_done()

  def run(self):
    logging.info('Running {}'.format(self.__class__.__name__))
    app = tornado.web.Application([])
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.spawn_callback(self.process)
    self.scheduler.schedule_all()
    io_loop.start()
