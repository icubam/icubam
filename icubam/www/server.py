import os.path
from absl import logging
import tornado.locale
from tornado import queues
import tornado.web
from icubam import base_server
from icubam.db import queue_writer
from icubam.www import updater
from icubam.www.handlers import db
from icubam.www.handlers import home
from icubam.www.handlers import plot
from icubam.www.handlers import static
from icubam.www.handlers import update
from icubam.www.handlers import upload_csv
from icubam.www.handlers.version import VersionHandler


class WWWServer(base_server.BaseServer):
  """Serves and manipulates the ICUBAM data."""

  def __init__(self, config, port=None):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.server.port
    self.writing_queue = queues.Queue()
    self.callbacks = [
      queue_writer.QueueWriter(self.writing_queue, self.db).process]
    self.path = home.HomeHandler.PATH

  def make_routes(self):
    self.add_handler(
      update.UpdateHandler,
      config=self.config, db=self.db, queue=self.writing_queue,
    )
    kwargs = dict(config=self.config, db=self.db)
    self.add_handler(home.HomeHandler, **kwargs)
    self.add_handler(home.MapByAPIHandler, **kwargs)
    self.add_handler(db.DBHandler, **kwargs)
    self.add_handler(VersionHandler, **kwargs)
    self.add_handler(
      upload_csv.UploadHandler, upload_path=self.config.server.upload_dir
    )
    self.add_handler(static.NoCacheStaticFileHandler, root=self.path)
    self.add_handler(plot.PlotHandler, **kwargs)

  def make_app(self, cookie_secret=None):
    # TODO(olivier): remove this when we have a backoffice.
    logging.info(self.debug_str)
    if cookie_secret is None:
      cookie_secret = self.config.SECRET_COOKIE
    self.make_routes()
    settings = {
      "cookie_secret": cookie_secret,
      "login_url": "/error",
    }
    tornado.locale.load_translations(os.path.join(self.path, 'translations'))
    return tornado.web.Application(self.routes, **settings)

  @property
  def debug_str(self):
    """Only for debug to be able to connect for now. To be removed."""
    return "\n".join(updater.Updater(self.config, self.db).get_urls())
