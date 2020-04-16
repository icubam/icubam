from absl import logging  # noqa: F401
import os.path
import tornado.locale
from tornado import queues
import tornado.web
from icubam import base_server
from icubam.db import queue_writer
from icubam.www.handlers import consent
from icubam.www.handlers import db
from icubam.www.handlers import home
from icubam.www.handlers import static
from icubam.www.handlers import update
from icubam.www.handlers import upload_csv
from icubam.www.handlers.version import VersionHandler
from icubam.www.handlers import error


class WWWServer(base_server.BaseServer):
  """Serves and manipulates the ICUBAM data."""
  def __init__(self, config, port=None):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.server.port
    self.writing_queue = queues.Queue()
    self.callbacks = [
      queue_writer.QueueWriter(self.writing_queue, self.db_factory).process
    ]
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
    self.add_handler(db.DBHandler, **kwargs)
    self.add_handler(VersionHandler, **kwargs)
    self.add_handler(consent.ConsentHandler, **kwargs)
    self.add_handler(
      upload_csv.UploadHandler, **{
        **kwargs,
        **{
          'upload_path': self.config.server.upload_dir
        }
      }
    )
    self.add_handler(static.NoCacheStaticFileHandler, root=self.path)
    self.add_handler(error.ErrorHandler, **kwargs)

  def make_app(self, cookie_secret=None):
    if cookie_secret is None:
      cookie_secret = self.config.SECRET_COOKIE
    self.make_routes()
    settings = {
      "cookie_secret": cookie_secret,
      "login_url": "/error",
    }
    tornado.locale.load_translations(os.path.join(self.path, "translations"))
    return tornado.web.Application(self.routes, **settings)
