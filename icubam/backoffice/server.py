import os.path

from absl import logging
import tornado.ioloop
import tornado.locale
import tornado.web

from icubam.backoffice.handlers.home import HomeBOHandler
from icubam.db import sqlite


class BackOfficeServer:
  """Serves and manipulates the Backoffice ICUBAM."""

  def __init__(self, config, port):
    self.config = config
    self.port = port if port is not None else self.config.backoffice.port
    self.routes = []
    self.db = sqlite.SQLiteDB(self.config.db.sqlite_path)
    self.make_app()

  def add_handler(self, handler, **kwargs):
    route = os.path.join("/", handler.ROUTE)
    self.routes.append((route, handler, kwargs))
    logging.info("{} serving on {}".format(handler.__name__, route))

  def make_app(self):
    self.add_handler(HomeBOHandler)

  def run(self):
    logging.info(
      "Running {} on port {}".format(self.__class__.__name__, self.port)
    )

    settings = {
      "cookie_secret": self.config.SECRET_COOKIE,
      "static_path": "icubam//www/static",
      "db": self.db
    }
    tornado.locale.load_translations('icubam/www/translations')
    app = tornado.web.Application(self.routes, **settings)
    app.listen(self.port)

    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.start()
