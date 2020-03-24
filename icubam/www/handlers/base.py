import tornado.web


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'id'

  def get_template_path(self):
    return 'icubam/www/templates/'

  def get_current_user(self):
    return self.get_secure_cookie(self.COOKIE)
