import os.path

from absl import logging
import tornado.ioloop
import tornado.locale
import tornado.web

from icubam.backoffice.handlers import home
from icubam import base_server


class BackOfficeServer(base_server.BaseServer):
  """Serves and manipulates the Backoffice ICUBAM."""

  def __init__(self, config, port):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.backoffice.port

  def make_routes(self):
    self.add_handler(home.HomeBOHandler, config=self.config, db=self.db)

  def make_app(self, cookie_secret=None):
    if cookie_secret is None:
      cookie_secret = self.config.SECRET_COOKIE
    settings = {
      "cookie_secret": cookie_secret,
      "static_path": "icubam/backoffice/static",
      "login_url": "/error",
    }
    tornado.locale.load_translations('icubam/backoffice/translations')
    self.make_routes()
    return tornado.web.Application(self.routes, **settings)
