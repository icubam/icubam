import tornado.web


class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
  ROUTE = r"/static/(.*)"
  PATH = "icubam/www/static/"

  def initialize(self, default_filename: str = None) -> None:
    super().initialize(path=self.PATH, default_filename=default_filename)

  def set_extra_headers(self, path):
    self.set_header(
      'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
