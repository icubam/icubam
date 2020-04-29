import collections
import dataclasses
import datetime
import os.path
from typing import Optional

import tornado.ioloop
import tornado.locale
import tornado.web
from absl import logging  # noqa: F401

from icubam import base_server, sentry
from icubam.backoffice.handlers import (
  bedcounts, consent, home, icus, login, logout, maps, messages,
  operational_dashboard, regions, tokens, upload, users
)
from icubam.analytics.analytics_server import register_analytics_callback


@dataclasses.dataclass
class ServerStatus:
  name: Optional[int] = None
  up: Optional[bool] = None
  started: Optional[str] = None
  last_ping: Optional[datetime.datetime] = None


class BackofficeApplication(tornado.web.Application):
  def __init__(self, config, db_factory, routes, root, **settings):
    self.config = config
    self.root = root
    self.db_factory = db_factory
    self.server_status = collections.defaultdict(ServerStatus)
    self.client = tornado.httpclient.AsyncHTTPClient()
    sentry.maybe_init_sentry(config, server_name='backoffice')
    super().__init__(routes, **settings)

    repeat_every = self.config.backoffice.ping_every * 1000
    pings = tornado.ioloop.PeriodicCallback(self.ping, repeat_every)
    pings.start()

    register_analytics_callback(self.config, db_factory, tornado.ioloop)

  async def ping(self):
    servers = {'server': 'www', 'messaging': 'sms'}
    for server, name in servers.items():
      url = self.config[server].base_url + 'health'
      status = self.server_status[server]
      status.name = name
      status.last_ping = datetime.datetime.utcnow()
      try:
        resp = await self.client.fetch(
          tornado.httpclient.HTTPRequest(url=url, request_timeout=1)
        )
        status.up = resp.code == 200
        status.started = resp.body
      except:
        status.up = False
        continue


class BackOfficeServer(base_server.BaseServer):
  """Serves and manipulates the Backoffice ICUBAM."""
  def __init__(self, config, port):
    super().__init__(config, port, root=config.backoffice.root)
    self.port = port if port is not None else self.config.backoffice.port

  def make_routes(self, path):
    self.add_handler(home.HomeHandler)
    self.add_handler(login.LoginHandler)
    self.add_handler(logout.LogoutHandler)
    self.add_handler(users.ListUsersHandler)
    self.add_handler(users.UserHandler)
    self.add_handler(users.ProfileHandler)
    self.add_handler(tokens.TokenHandler)
    self.add_handler(tokens.ListTokensHandler)
    self.add_handler(icus.ListICUsHandler)
    self.add_handler(icus.ICUHandler)
    self.add_handler(regions.ListRegionsHandler)
    self.add_handler(regions.RegionHandler)
    self.add_handler(bedcounts.ListBedCountsHandler)
    self.add_handler(operational_dashboard.OperationalDashHandler)
    self.add_handler(messages.ListMessagesHandler)
    self.add_handler(maps.MapsHandler)
    self.add_handler(upload.UploadHandler)
    self.add_handler(consent.ConsentResetHandler)

    if os.path.isdir(self.config.backoffice.extra_plots_dir):
      route = os.path.join("/", self.root, r'static/extra-plots/(.*)')
      self.routes.append((
        route, tornado.web.StaticFileHandler, {
          'path': self.config.backoffice.extra_plots_dir
        }
      ))

    for folder in ['dist', 'plugins', 'static']:
      route = os.path.join("/", self.root, folder, r'(.*)')
      folder = '' if folder == 'static' else folder
      self.routes.append((
        route, tornado.web.StaticFileHandler, {
          'path': os.path.join(path, 'static', folder)
        }
      ))
    # Those are to get the js of the map page and the favicons
    route_pattern = os.path.join("/", self.root, r'www/static/(.*)')
    for route in [r'/(favicon.icon)', route_pattern]:
      self.routes.append((
        route, tornado.web.StaticFileHandler, {
          'path': os.path.join(path, '../www/static')
        }
      ))

  def make_app(self, cookie_secret=None):
    if cookie_secret is None:
      cookie_secret = self.config.SECRET_COOKIE
    path = os.path.dirname(os.path.abspath(__file__))
    settings = {
      'cookie_secret': cookie_secret,
      'login_url': 'login',
    }
    tornado.locale.load_translations(os.path.join(path, 'translations'))
    self.make_routes(path)
    logging.info(
      'Access the backoffice at http://localhost:{}/{}/'.format(
        self.port, self.config.backoffice.root
      )
    )

    return BackofficeApplication(
      self.config, self.db_factory, self.routes, self.root, **settings
    )
