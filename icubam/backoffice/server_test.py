from unittest import mock
import tornado.testing
import urllib

from icubam import config
from icubam.backoffice import server
from icubam.backoffice.handlers import (home, login, logout)


class ServerTestCase(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG, mode='dev')
    self.server = server.BackOfficeServer(self.config, port=8889)
    super().setUp()

  def get_app(self):
    return self.server.make_app(cookie_secret='secret')

  def test_homepage_without_cookie(self):
    response = self.fetch(home.HomeHandler.ROUTE)
    self.assertEqual(response.code, 200)

  def test_login(self):
    response = self.fetch(login.LoginHandler.ROUTE)
    self.assertEqual(response.code, 200)

  def test_login_with_error(self):
    error_reason = "failure"
    path = "{0}?error={1}".format(login.LoginHandler.ROUTE, error_reason)
    response = self.fetch(path)
    self.assertTrue(error_reason in response.effective_url)

  def test_logout(self):
    response = self.fetch(logout.LogoutHandler.ROUTE)
    self.assertEqual(response.code, 200)
