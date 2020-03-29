from unittest import mock
import tornado.testing
from icubam import config
from icubam.backoffice import server
from icubam.backoffice.handlers import home


class ServerTestCase(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG, mode='dev')
    self.server = server.BackOfficeServer(self.config, port=8889)
    super().setUp()

  def get_app(self):
    return self.server.make_app(cookie_secret='secret')

  def test_homepage_without_cookie(self):
    response = self.fetch(home.HomeBOHandler.ROUTE)
    self.assertEqual(response.code, 200)
