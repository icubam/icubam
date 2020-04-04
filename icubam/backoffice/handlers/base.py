import tornado.httpclient
import tornado.locale
import tornado.web
from typing import List, Dict, Union
from icubam.db.store import create_store_for_sqlite_db


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'user'

  def initialize(self, config, db):
    self.config = config
    self.db = db
    self.user = None
    self.client = tornado.httpclient.AsyncHTTPClient()

  async def ping(self):
    result = {'server': False, 'messaging': False}
    for server in result.keys():
      url = self.config[server].base_url + 'health'
      try:
        resp = await self.client.fetch(
          tornado.httpclient.HTTPRequest(url=url, request_timeout=1))
        result[server] = resp.code == 200
      except:
        continue
    result['www'] = result.pop('server')
    return result

  async def render(self, path, **kwargs):
    pings = await self.ping()

    super().render(path, this_user=self.user, pings=pings, **kwargs)

  def get_template_path(self):
    return 'icubam/backoffice/templates/'

  def get_current_user(self):
    if self.user is not None:
      return self.user

    userid = self.get_secure_cookie(self.COOKIE)
    if not userid:
      return None

    self.user = self.db.get_user(int(tornado.escape.json_decode(userid)))
    return self.user

  def get_user_locale(self):
    locale = self.get_query_argument('hl', default=self.config.default_locale)
    # We fallback to Accept-Language header.
    return tornado.locale.get(locale) if locale else None

  def set_default_headers(self):
    self.set_header("Access-Control-Allow-Credentials", True)
    self.set_header("Access-Control-Allow-Origin", "*")
    self.set_header(
        "Access-Control-Allow-Headers", "x-requested-with, Content-Type")
    self.set_header(
        'Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')

  async def options(self):
    self.set_status(200)
    self.finish()

  def parse_from_body(self, cls) -> dict:
    """Given a store class, parse the body a dictionary."""
    result = dict()
    for col in cls.get_column_names():
      value = self.get_body_arguments(col + '[]', None)
      if not value:
        value = self.get_body_argument(col, None)
      if value is not None:
        result[col] = value
    return result

  def format_list_item(self, item: Union[Dict, List]) -> list:
    """Prepare a dictionary representing a row of a table for display."""
    # TODO(olivier) improve this, too hard coded
    auto_links = {f'{k}_id': k for k in ['icu', 'user', 'region']}
    auto_links['external_client_id'] = 'token'
    result = item
    if not isinstance(item, list):
      result = []
      for k, v in item.items():
        route = auto_links.get(k, None)
        link = '/{}?id={}'.format(route, v) if route is not None else False
        result.append({'key': k, 'value': v, 'link': link})
    return result


class AdminHandler(BaseHandler):
  """A base handler for admin only routes."""

  def get_current_user(self):
    user = super().get_current_user()
    if user is None or not user.is_admin:
      return None
    else:
      return user
