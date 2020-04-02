import tornado.testing
from unittest import mock

from icubam import config
from icubam.backoffice import server
from icubam.backoffice.handlers import (
  base, home, login, logout, users, tokens, icus, dashboard, plot, regions)


class ServerTestCase(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG, mode='dev')
    self.server = server.BackOfficeServer(self.config, port=8889)
    userid = self.server.db.add_default_admin()
    self.user = self.server.db.get_user(userid)
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

  def test_homepage_without(self):
    handlers = [
      icus.ListICUsHandler, icus.ICUHandler,
      users.ListUsersHandler, users.UserHandler,
      tokens.ListTokensHandler, tokens.TokenHandler,
      regions.ListRegionsHandler, regions.RegionHandler,
      dashboard.ListBedCountsHandler, plot.PlotHandler,
      ]
    for handler in handlers:
      with mock.patch.object(handler, 'get_current_user') as m:
        m.return_value = self.user
      response = self.fetch(handler.ROUTE, method='GET')
    self.assertEqual(response.code, 200, msg=handler.__name__)
