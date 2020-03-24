import tornado.web


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'id'

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Credentials", True)
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header(
        "Access-Control-Allow-Headers", "x-requested-with, Content-Type")
    self.set_header(
        'Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')

  def get_template_path(self):
    return 'icubam/www/templates/'

  def get_current_user(self):
    return self.get_secure_cookie(self.COOKIE)
