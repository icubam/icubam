from absl import logging
import os.path
import tornado.ioloop
import tornado.web
from icubam.db import sqlite


class BaseServer:
  """Base class for ICUBAM servers."""

  def __init__(self, config, port):
    self.config = config
    self.port = port
    self.routes = []
    self.db = sqlite.SQLiteDB(self.config.db.sqlite_path)
    self.routes = []
    self.callbacks = []

  def add_handler(self, handler, **kwargs):
    route = os.path.join("/", handler.ROUTE)
    self.routes.append((route, handler, kwargs))
    logging.info("{}: {} serving on {}".format(
      self.__class__.__name__, handler.__name__, route))

  def make_app(self) -> tornado.web.Application:
    return tornado.web.Application(self.routes)

  def run(self):
    logging.info(
      "{} running on port {}".format(self.__class__.__name__, self.port)
    )
    app = self.make_app()
    app.listen(self.port)
    io_loop = tornado.ioloop.IOLoop.current()
    for callback_obj in self.callbacks:
      io_loop.spawn_callback(callback_obj.process)
    io_loop.start()
