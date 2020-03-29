from absl import logging
import os.path
import tornado.ioloop
import tornado.locale
from tornado import queues
import tornado.web

from icubam.db import queue_writer
from icubam.db import sqlite
from icubam.messaging import scheduler
from icubam.www import token
from icubam.www.handlers import db
from icubam.www.handlers import home
from icubam.www.handlers import show
from icubam.www.handlers import static
from icubam.www.handlers import update
from icubam.www.handlers import upload_csv


class WWWServer:
  """Serves and manipulates the ICUBAM data."""

  def __init__(self, config, port):
    self.config = config
    self.port = port
    self.routes = []
    self.token_encoder = token.TokenEncoder(self.config)
    self.writing_queue = queues.Queue()
    self.db = sqlite.SQLiteDB(self.config.db.sqlite_path)
    self.callbacks = [queue_writer.QueueWriter(self.writing_queue, self.db)]

  def add_handler(self, handler, **kwargs):
    route = os.path.join("/", handler.ROUTE)
    self.routes.append((route, handler, kwargs))
    logging.info("{} serving on {}".format(handler.__name__, route))

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

  def run(self):
    logging.info(
      "Running {} on port {}".format(self.__class__.__name__, self.port)
    )
    logging.info(self.debug_str)

    app = self.make_app()
    app.listen(self.port)

    io_loop = tornado.ioloop.IOLoop.current()
    for callback_obj in self.callbacks:
      io_loop.spawn_callback(callback_obj.process)

    io_loop.start()
