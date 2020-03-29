import os.path

import tornado.ioloop
import tornado.locale
import tornado.web
from absl import logging
from tornado_sqlalchemy import SQLAlchemy

from icubam.backoffice.handlers.home import HomeBOHandler
from icubam.backoffice.handlers.user import ListUserHandler, UserJson, AddUserHandler


class BackOfficeServer:
  """Serves and manipulates the Backoffice ICUBAM."""

  def __init__(self, config, port):
    self.config = config
    self.port = port
    self.routes = []
    self.db = SQLAlchemy("sqlite+pysqlite:///{}".format(self.config.db.sqlite_path))
    self.make_app()

  def add_handler(self, handler, **kwargs):
    route = os.path.join("/", handler.ROUTE)
    self.routes.append((route, handler, kwargs))
    logging.info("{} serving on {}".format(handler.__name__, route))

  def make_app(self):
    self.add_handler(HomeBOHandler)
    self.add_handler(ListUserHandler)
    self.add_handler(UserJson)
    self.add_handler(AddUserHandler)

  def run(self):
    logging.info(
      "Running {} on port {}".format(self.__class__.__name__, self.port)
    )

    settings = {
      "cookie_secret": self.config.SECRET_COOKIE,
      "static_path": "icubam/backoffice/static",
      "db": self.db
    }
    tornado.locale.load_translations('icubam/www/translations')
    app = tornado.web.Application(self.routes, **settings)
    app.listen(self.port)

    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.start()
