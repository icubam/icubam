from unittest import mock
import tornado.testing
from icubam import config
from icubam.www import server
from icubam.www import token
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www.handlers import update


class TestWWWServer(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG, mode='dev')
    super().setUp()

  def get_app(self):
    www_server = server.WWWServer(self.config, port=8888)
    return www_server.make_app()

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
    self.assertEqual(response.code, 400)

    encoder = token.TokenEncoder(self.config)
    response = self.fetch(url_prefix + encoder.encode_icu('test_icu', 123))
    self.assertEqual(response.code, 200)
