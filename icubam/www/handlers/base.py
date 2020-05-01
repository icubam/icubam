from absl import logging
import functools
import os.path
import tornado.locale
import tornado.web

from icubam import authenticator
from icubam.db import store


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'id'
  PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

  def initialize(self, config, db_factory):
    self.config = config
    self.db = db_factory.create()
    self.user = None
    self.authenticator = authenticator.Authenticator(self.config, self.db)

  def get_template_path(self):
    return os.path.join(self.PATH, 'templates/')

  def get_current_user(self):
    user_token = self.get_secure_cookie(self.COOKIE)
    if user_token is None:
      return None

    user_icu = self.authenticator.authenticate(user_token)
    if user_icu is None:
      return None

    self.user, self.icu = user_icu
    return self.user

  def get_user_locale(self):
    # We fallback to Accept-Language header.
    locale_code = self.get_query_argument('hl', default=None)
    if locale_code is None:
      return self.get_browser_locale()
    else:
      return tornado.locale.get(locale_code)


def authenticated(func=None, *, code=503):
  """Return a given HTTP code instead of redirecting in case the user is not
  authenticated (unlike tornado.web.authenticated)"""
  if func is None:
    return functools.partial(authenticated, code=code)

  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    if not self.current_user:
      return self.set_status(code)
    return func(self, *args, **kwargs)

  return wrapper


class APIKeyProtectedHandler(BaseHandler):
  """A base handler for API KEY accessible routes."""

  # Must be redefined in subclass
  ACCESS = [store.AccessTypes.ALL]

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      logging.info('no API_KEY')
      return

    client = self.db.auth_external_client(key)
    if client is None:
      logging.info(f'Unknown API key {key}')
      return None

    if client.access_type in self.ACCESS:
      self.regions = client.regions
      return client
    else:
      logging.info('Unauthorized route.')
      return None
