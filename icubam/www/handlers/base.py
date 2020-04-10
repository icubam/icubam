import os.path
import tornado.locale
import tornado.web

from icubam.db import store


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'id'
  PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

  def initialize(self, config, db_factory):
    self.config = config
    self.db = db_factory.create()

  def get_template_path(self):
    return os.path.join(self.PATH, 'templates/')

  def get_current_user(self):
    return self.get_secure_cookie(self.COOKIE)

  def get_user_locale(self):
    locale = self.get_query_argument('hl', default=self.config.default_locale)
    # We fallback to Accept-Language header.
    return tornado.locale.get(locale) if locale else None


class APIKeyProtectedHandler(BaseHandler):
  """A base handler for API KEY accessible routes."""

  # Must be redefined in subclass
  ACCESS = [store.AccessTypes.ALL]

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      return

    client = self.db.auth_external_client(key)
    if client is None:
      return None

    if client.access_type in self.ACCESS:
      return client.external_client_id
    else:
      return None
