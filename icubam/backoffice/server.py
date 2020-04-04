import os.path

from absl import logging  # noqa: F401
import tornado.ioloop
import tornado.locale
import tornado.web

from icubam.backoffice.handlers import (
  home, login, logout, users, tokens, icus, dashboard, plot, regions, messages)
from icubam import base_server


class BackOfficeServer(base_server.BaseServer):
  """Serves and manipulates the Backoffice ICUBAM."""

  def __init__(self, config, port):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.backoffice.port

  def make_routes(self, path):
    kwargs = dict(config=self.config, db=self.db)
    self.add_handler(home.HomeHandler, **kwargs)
    self.add_handler(login.LoginHandler, **kwargs)
    self.add_handler(logout.LogoutHandler, **kwargs)
    self.add_handler(users.ListUsersHandler, **kwargs)
    self.add_handler(users.UserHandler, **kwargs)
    self.add_handler(users.ProfileHandler, **kwargs)
    self.add_handler(tokens.TokenHandler, **kwargs)
    self.add_handler(tokens.ListTokensHandler, **kwargs)
    self.add_handler(icus.ListICUsHandler, **kwargs)
    self.add_handler(icus.ICUHandler, **kwargs)
    self.add_handler(regions.ListRegionsHandler, **kwargs)
    self.add_handler(regions.RegionHandler, **kwargs)
    self.add_handler(dashboard.ListBedCountsHandler, **kwargs)
    self.add_handler(plot.PlotHandler, **kwargs)
    self.add_handler(messages.ListMessagesHandler, **kwargs)

    for folder in ['dist', 'pages', 'plugins']:
      self.routes.append(
        (
          r"/{}/(.*)".format(folder),
          tornado.web.StaticFileHandler,
          {"path": os.path.join(path, 'static', folder)}
        )
      )


  def make_app(self, cookie_secret=None):
    if cookie_secret is None:
      cookie_secret = self.config.SECRET_COOKIE
    path = os.path.dirname(os.path.abspath(__file__))
    settings = {
      "cookie_secret": cookie_secret,
      "static_path": os.path.join(path, 'static'),
      "login_url": "/login",
    }
    tornado.locale.load_translations(os.path.join(path, 'translations'))
    self.make_routes(path)
    return tornado.web.Application(self.routes, **settings)
