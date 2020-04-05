from absl import logging  # noqa: F401
import collections
import dataclasses
import datetime
import os.path
import tornado.ioloop
import tornado.locale
import tornado.web
from typing import Dict
import tornado.ioloop
from icubam.backoffice.handlers import (
  home, login, logout, users, tokens, icus, dashboard, operational_dashboard,
  messages, regions)
from icubam import base_server


@dataclasses.dataclass
class ServerStatus:
  name: int = None
  up: bool = None
  started: str = None
  last_ping: datetime.datetime = None


class BackofficeApplication(tornado.web.Application):
  def __init__(self, config, db, routes, **settings):
    self.config = config
    self.db = db
    self.server_status = collections.defaultdict(ServerStatus)
    super().__init__(routes, **settings)

    repeat_every = self.config.backoffice.ping_every * 1000
    pings = tornado.ioloop.PeriodicCallback(self.ping, repeat_every)
    pings.start()

  async def ping(self):
    servers = {'server': 'www', 'messaging': 'sms'}
    for server, name in servers.items():
      url = self.config[server].base_url + 'health'
      status = self.server_status[server]
      status.name = name
      status.last_ping = datetime.datetime.utcnow()
      try:
        resp = await self.client.fetch(
          tornado.httpclient.HTTPRequest(url=url, request_timeout=1))
        status.up = resp.code == 200
        status.started = resp.body
      except:
        status.up = False
        continue


class BackOfficeServer(base_server.BaseServer):
  """Serves and manipulates the Backoffice ICUBAM."""

  def __init__(self, config, port):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.backoffice.port
    self.client = tornado.httpclient.AsyncHTTPClient()

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
    self.add_handler(operational_dashboard.OperationalDashHandler, **kwargs)
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

    return BackofficeApplication(self.config, self.db, self.routes, **settings)
