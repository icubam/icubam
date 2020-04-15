import json
import tornado.testing
from unittest import mock

from icubam import config
from icubam.backoffice import server
from icubam.backoffice.handlers import (
  base, home, login, logout, users, tokens, icus, bedcounts,
  operational_dashboard, regions, maps, consent
)


class ServerTestCase(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG, mode='dev')
    self.server = server.BackOfficeServer(self.config, port=8889)
    self.db = self.server.db_factory.create()
    self.admin_id = self.db.add_default_admin()
    self.admin = self.db.get_user(self.admin_id)
    self.user = self.db.get_user(self.admin_id)
    self.app = self.get_app()
    super().setUp()

  def get_app(self):
    return self.server.make_app(cookie_secret='secret')

  def fetch(self, url, follow_redirects=False, **kwargs):
    prefix = '/' + self.app.root + '/'
    path = prefix + url.lstrip('/')
    return super().fetch(path, follow_redirects=follow_redirects, **kwargs)

  def test_homepage_without_cookie(self):
    response = self.fetch(home.HomeHandler.ROUTE, follow_redirects=True)
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
    response = self.fetch(logout.LogoutHandler.ROUTE, follow_redirects=True)
    self.assertEqual(response.code, 200)

  def test_homepage_without(self):
    handlers = [
      icus.ListICUsHandler,
      icus.ICUHandler,
      users.ListUsersHandler,
      users.UserHandler,
      tokens.ListTokensHandler,
      tokens.TokenHandler,
      regions.ListRegionsHandler,
      regions.RegionHandler,
      bedcounts.ListBedCountsHandler,
      operational_dashboard.OperationalDashHandler,
      #TODO this test fails, probably because the message server is not started
      #messages.ListMessagesHandler,
      maps.MapsHandler,
    ]
    for handler in handlers:
      with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
        m.return_value = self.user
        response = self.fetch(handler.ROUTE, method='GET')
        self.assertEqual(response.code, 200, msg=handler.__name__)

  def test_operational_dashboard(self):
    handler = operational_dashboard.OperationalDashHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.user
      response = self.fetch(handler.ROUTE + '?region=1', method='GET')
      self.assertEqual(response.code, 200, msg=handler.__name__)

  def test_consent_reset(self):
    handler = consent.ConsentResetHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.admin
      response = self.fetch(
        handler.ROUTE, method='POST', body=json.dumps(self.user.user_id)
      )
    self.assertEqual(response.code, 200)
    resp_data = json.loads(response.body)
    self.assertIn('error', resp_data)
    self.assertIn('msg', resp_data)
    self.assertIsNone(resp_data['error'])
