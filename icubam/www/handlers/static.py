import tornado.web


class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
  ROUTE = r"/static/(.*)"
  PATH = "icubam/www/static/"

  def initialize(self, default_filename: str = None) -> None:
    super().initialize(path=self.PATH, default_filename=default_filename)
