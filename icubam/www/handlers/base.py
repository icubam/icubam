from absl import logging
import functools
import os.path
import tornado.locale
import tornado.web
from typing import Tuple, Optional

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

  def decode_token(
    self, user_token: str
  ) -> Tuple[Optional[store.User], Optional[store.ICU]]:
    """Returns the user object and the icu object encoded in the token."""
    input_data = self.token_encoder.decode(user_token)
    if input_data is None:
      logging.error("No token to be found.")
      return None, None

    try:
      userid, icuid = input_data
    except Exception as e:
      logging.error(f'Token is not a 2-tuple as expected: {e}')
      userid, icuid = None, None
      if isinstance(input_data, dict):
        userid = input_data.get('user_id', None)
        icuid = input_data.get('icu_id', None)

    user = self.db.get_user(userid)
    if user is None:
      logging.error(f"User does not exist.")
      return None, None

    if user.consent is not None and not user.consent:
      logging.error(f"User has bailed out from ICUBAM.")
      return None, None

    user_icu_ids = {i.icu_id: i for i in user.icus}
    icu = user_icu_ids.get(icuid, None)
    if icu is None:
      logging.error(f"User does not belong the ICU.")
      return None, None

    return user, icu

  def get_template_path(self):
    return os.path.join(self.PATH, 'templates/')

  def get_current_user(self):
    user_token = self.get_secure_cookie(self.COOKIE)
    if user_token is None:
      return None

    self.user, self.icu = self.decode_token(user_token)
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
    return func(*args, **kwargs)

  return wrapper


class APIKeyProtectedHandler(BaseHandler):
  """A base handler for API KEY accessible routes."""

  # Must be redefined in subclass
  ACCESS = [store.AccessTypes.ALL]

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      self.set_status(503)
      return

    client = self.db.auth_external_client(key)
    if client is None:
      self.set_status(503)
      return None

    if client.access_type in self.ACCESS:
      self.regions = client.regions
      return client
    else:
      self.set_status(503)
      return None
