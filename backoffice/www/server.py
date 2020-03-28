import os.path

import tornado.ioloop
import tornado.locale
import tornado.web
from absl import logging
from sqlalchemy import create_engine
from tornado_sqlalchemy import SQLAlchemy

from backoffice.model.user import Base
from backoffice.www.handlers.login import LoginHandler
from backoffice.www.handlers.user import ListUserHandler, UserJson, CreateUserHandler


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
    self.add_handler(LoginHandler)
    self.add_handler(ListUserHandler)
    self.add_handler(UserJson)
    self.add_handler(CreateUserHandler)

  def run(self):
    logging.info(
      "Running {} on port {}".format(self.__class__.__name__, self.port)
    )
    engine = create_engine("sqlite+pysqlite:///{}".format(self.config.db.sqlite_path), encoding='utf-8', echo=True)
    Base.metadata.create_all(engine)

    settings = {
      "cookie_secret": self.config.SECRET_COOKIE,
      "login_url": "/login",
      "static_path": "backoffice/www/static",
      "db": self.db
    }
    tornado.locale.load_translations('icubam/www/translations')
    app = tornado.web.Application(self.routes, **settings)
    app.listen(self.port)

    io_loop = tornado.ioloop.IOLoop.current()
    # for callback_obj in self.callbacks:
    # io_loop.spawn_callback(callback_obj.process)
    io_loop.start()
