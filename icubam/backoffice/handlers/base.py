import tornado.locale
import tornado.web


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'user'

  def initialize(self, config, db):
    self.config = config
    self.db = db

  def get_template_path(self):
    return 'icubam/backoffice/templates/'

  def get_current_user(self):
    return self.get_secure_cookie(self.COOKIE)

  def get_user_locale(self):
    locale = self.get_query_argument('hl', default=self.config.locale)
    # We fallback to Accept-Language header.
    return tornado.locale.get(locale) if locale else None
