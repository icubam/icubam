import json
from unittest import mock
import tornado.testing
from icubam import config
from icubam.db import store
from icubam.www import server
from icubam.www import token
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www.handlers import update
from icubam.www.handlers.version import VersionHandler


class TestWWWServer(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG, mode='dev')
    self.server = server.WWWServer(self.config, port=8888)
    super().setUp()
    self.db = self.server.db_factory.create()
    self.admin_id = self.db.add_default_admin()
    self.icu_id = self.db.add_icu(self.admin_id, store.ICU(name='icu'))
    self.user_id = self.db.add_user_to_icu(
      self.admin_id, self.icu_id,
      store.User(name='user', consent=True, is_active=True)
    )
    self.user = self.db.get_user(self.user_id)
    self.icu = self.db.get_icu(self.icu_id)

  def get_app(self):
    return self.server.make_app(cookie_secret='secret')

  def test_homepage_without_cookie(self):
    response = self.fetch(home.HomeHandler.ROUTE)
    self.assertEqual(response.code, 404)

  def test_homepage_with_cookie(self):
    """If there is a cookie, the route is reachable."""
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = 'anything'
      response = self.fetch(home.HomeHandler.ROUTE, method='GET')
    self.assertEqual(response.code, 200)

  def test_update_form(self):
    response = self.fetch(update.UpdateHandler.ROUTE)
    self.assertEqual(response.code, 400)

    url_prefix = "{}?id=".format(update.UpdateHandler.ROUTE)
    response = self.fetch(url_prefix + "123")
    self.assertEqual(response.code, 404)

    encoder = token.TokenEncoder(self.config)
    jwt = encoder.encode_data(self.user, self.icu)
    response = self.fetch(url_prefix + jwt)
    self.assertEqual(response.code, 200)

  def test_version(self):
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = 'anything'
      response = self.fetch(VersionHandler.ROUTE)
    self.assertEqual(response.code, 200)
    body = json.loads(response.body)
    self.assertEqual(set(body.keys()), {'data'})
    self.assertEqual(
      set(body['data'].keys()),
      {'version', 'git-hash', 'bed_counts.last_modified'}
    )
