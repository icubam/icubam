import os.path
import tornado.locale
import tornado.web

from icubam.db import store
from icubam.www import token


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'id'
  PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

  def initialize(self, config, db_factory):
    self.config = config
    self.db = db_factory.create()
    self.user = None
    self.token_encoder = token.TokenEncoder(self.config)

  def get_template_path(self):
    return os.path.join(self.PATH, 'templates/')

  def get_current_user(self):
    encoded_data = self.get_secure_cookie(self.COOKIE)
    if encoded_data is None:
      return None

    data = self.token_encoder.decode(encoded_data)
    userid = int(data.get('user_id', -1))
    self.user = self.db.get_user(userid)
    if self.user:
      # User who bailed out have no access to ICUBAM
      # User with unknown consent have access until they decide.
      if self.user.consent is None or self.user.consent:
        return self.user.user_id

  def get_user_locale(self):
    # We fallback to Accept-Language header.
    locale_code = self.get_query_argument('hl', default=None)
    if locale_code is None:
      return self.get_browser_locale()
    else:
      return tornado.locale.get(locale_code)


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
      self.regions = client.regions
      return client.external_client_id
    else:
      return None
