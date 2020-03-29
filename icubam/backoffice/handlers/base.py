import tornado.locale
import tornado.web


class BaseBOHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  def get_template_path(self):
    return 'icubam/backoffice/templates/'

  def get_current_user(self):
    return self.get_secure_cookie("user")

  def get_user_locale(self):
    locale = self.get_query_argument('hl', default=None)
    # We fallback to Accept-Language header.
    return tornado.locale.get(locale) if locale else None
