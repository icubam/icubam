import os.path

import tornado.locale
import tornado.web
from absl import logging  # noqa: F401
from tornado import queues

from icubam import base_server, sentry
from icubam.analytics import client
from icubam.db import queue_writer
from icubam.www.handlers import consent, db, error, disclaimer, home, static, update
from icubam.www.handlers.version import VersionHandler


class WWWServer(base_server.BaseServer):
  """Serves and manipulates the ICUBAM data."""
  def __init__(self, config, port=None):
    sentry.maybe_init_sentry(config, server_name='www')
    super().__init__(config, port)
    self.port = port if port is not None else self.config.server.port
    self.writing_queue = queues.Queue()
    self.callbacks = [
      queue_writer.QueueWriter(self.writing_queue, self.db_factory).process
    ]
    self.analytics_client = client.AnalyticsClient(config)
    self.path = home.HomeHandler.PATH

  def make_routes(self):
    self.routes.append((
      r'/(favicon.ico)', tornado.web.StaticFileHandler, {
        'path': os.path.join(self.path, 'static')
      }
    ))
    self.add_handler(
      update.UpdateBedCountsHandler,
      config=self.config,
      db_factory=self.db_factory,
      queue=self.writing_queue,
    )
    kwargs = dict(config=self.config, db_factory=self.db_factory)
    self.add_handler(update.UpdateHandler, **kwargs)
    self.add_handler(home.HomeHandler, **kwargs)
    self.add_handler(home.MapByAPIHandler, **kwargs)
    self.add_handler(
      db.DBHandler, **{
        **kwargs,
        **{
          'upload_path': self.config.server.upload_dir,
          'client': self.analytics_client,
        }
      }
    )
    self.add_handler(db.OperationalDashboardHandler, **kwargs)
    self.add_handler(VersionHandler, **kwargs)
    self.add_handler(consent.ConsentHandler, **kwargs)
    self.add_handler(error.ErrorHandler, **kwargs)
    self.add_handler(disclaimer.DisclaimerHandler, **kwargs)

    if os.path.isdir(self.config.backoffice.extra_plots_dir):
      prefix = db.OperationalDashboardHandler.BACKOFFICE_PREFIX
      self.routes.append((
        f'/{prefix}static/extra-plots/(.*)', tornado.web.StaticFileHandler, {
          'path': self.config.backoffice.extra_plots_dir
        }
      ))
      parent = os.path.join('/', '/'.join(os.path.split(self.path)[:-1]))
      bo_path = os.path.join(parent, 'backoffice/static/dist')
      self.routes.append((
        '/static/dist/(.*)', tornado.web.StaticFileHandler, {
          'path': bo_path
        }
      ))

    self.add_handler(static.NoCacheStaticFileHandler, root=self.path)

  def make_app(self, cookie_secret=None):
    if cookie_secret is None:
      cookie_secret = self.config.SECRET_COOKIE
    self.make_routes()
    settings = {"cookie_secret": cookie_secret, "login_url": "/error"}
    tornado.locale.load_translations(os.path.join(self.path, "translations"))
    return tornado.web.Application(self.routes, **settings)
