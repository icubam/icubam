import os.path
import tornado.web


class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
  ROUTE = r"/static/(.*)"
  PATH = "static/"

  def initialize(self, root, default_filename: str = None) -> None:
    super().initialize(path=os.path.join(root, self.PATH),
                       default_filename=default_filename)
