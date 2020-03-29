from absl import logging
import tornado.locale
from tornado import queues
import tornado.web
from icubam import base_server
from icubam.db import queue_writer
from icubam.messaging import scheduler
from icubam.www import token
from icubam.www.handlers import db
from icubam.www.handlers import home
from icubam.www.handlers import show
from icubam.www.handlers import static
from icubam.www.handlers import update
from icubam.www.handlers import upload_csv


class WWWServer(base_server.BaseServer):
  """Serves and manipulates the ICUBAM data."""

  def __init__(self, config, port=None):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.server.port
    self.token_encoder = token.TokenEncoder(self.config)
    self.writing_queue = queues.Queue()
    self.callbacks = [
      queue_writer.QueueWriter(self.writing_queue, self.db).process]

  def make_routes(self):
    self.add_handler(
      update.UpdateHandler,
      config=self.config,
      db=self.db,
      queue=self.writing_queue,
      token_encoder=self.token_encoder,
    )
    self.add_handler(home.HomeHandler, config=self.config, db=self.db)
    self.add_handler(show.ShowHandler, config=self.config, db=self.db)
    self.add_handler(show.DataJson, config=self.config, db=self.db)
    self.add_handler(db.DBHandler, config=self.config, db=self.db)
    self.add_handler(
      upload_csv.UploadHandler, upload_path=self.config.server.upload_dir
    )
    self.add_handler(static.NoCacheStaticFileHandler)

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
    tornado.locale.load_translations('icubam/www/translations')
    return tornado.web.Application(self.routes, **settings)

  @property
  def debug_str(self):
    """Only for debug to be able to connect for now. To be removed."""
    schedule = scheduler.MessageScheduler(
      self.db, None, self.token_encoder, base_url=self.config.server.base_url)
    return "\n".join(schedule.urls)
