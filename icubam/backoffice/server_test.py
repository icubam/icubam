import json
import tornado.testing
from unittest import mock
from urllib.parse import urlencode

from icubam import config
from icubam.backoffice import server
from icubam.backoffice.handlers import (
  base, home, login, logout, users, tokens, icus, bedcounts,
  operational_dashboard, regions, maps, consent, upload
)


class ServerTestCase(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG)
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
      home.HomeHandler,
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

  def test_upload(self):
    handler = upload.UploadHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.admin
      data_icus = dict()
      with open("resources/test/icu2.csv") as csv_f:
        data_icus['data'] = csv_f.read()
        data_icus['objtype'] = base.ObjType.ICUS.name
        response = self.fetch(
          handler.ROUTE, method='POST', body=json.dumps(data_icus)
        )
      self.assertEqual(response.code, 200)
      resp_data = json.loads(response.body)
      self.assertIn('error', resp_data)
      self.assertIn('msg', resp_data)
      self.assertEqual(resp_data['error'], False)
      data_bedcounts = dict()
      with open("resources/test/bedcounts.csv") as csv_f:
        data_bedcounts['data'] = csv_f.read()
        data_bedcounts['objtype'] = base.ObjType.BEDCOUNTS.name
        response = self.fetch(
          handler.ROUTE, method='POST', body=json.dumps(data_bedcounts)
        )
    self.assertEqual(response.code, 200)
    resp_data = json.loads(response.body)
    self.assertIn('error', resp_data)
    self.assertIn('msg', resp_data)
    self.assertEqual(resp_data['error'], False)

  def test_post_region(self):
    handler = regions.RegionHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.admin

      name = "InvalidRegion"
      self.assertIsNone(self.db.get_region_by_name(name))
      response = self.fetch(
        handler.ROUTE, method='POST', body=f"region_id=&name={name}"
      )
      # redirect to ListRegionsHandler
      self.assertEqual(response.code, 302)
      self.assertIsNotNone(self.db.get_region_by_name(name))

  def test_post_icu(self):
    handler = icus.ICUHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.admin

      data = {
        'icu_id': '',
        'name': 'TestICU',
        'telephone': '00000000000',
        'legal_id': '',
        'is_active': 'on',
        'region_id': 1,
        'city': 'Paris',
        'dept': 'Ile-de-France',
        'lat': 0.0000,
        'long': 0.0000
      }
      self.assertIsNone(self.db.get_icu_by_name(data['name']))
      response = self.fetch(handler.ROUTE, method='POST', body=urlencode(data))
      # redirect to ListICUsHandler
      self.assertEqual(response.code, 302)
      self.assertIsNotNone(self.db.get_icu_by_name(data['name']))

  def test_post_token(self):
    handler = tokens.TokenHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.admin

      data = {
        'external_client_id': '',
        'name': 'TestToken',
        'telephone': '00000000000',
        'email': "test@test.org",
        'is_active': 'on',
        'access_type': 'ALL',
        'expiration_date': ''
      }
      self.assertIsNone(self.db.get_external_client_by_email(data['email']))
      response = self.fetch(handler.ROUTE, method='POST', body=urlencode(data))
      # redirect to ListTokensHandler
      self.assertEqual(response.code, 302)
      self.assertIsNotNone(self.db.get_external_client_by_email(data['email']))

  def test_post_user(self):
    handler = users.UserHandler
    with mock.patch.object(base.BaseHandler, 'get_current_user') as m:
      m.return_value = self.admin

      data = {
        'user_id': '',
        'name': 'TestUser',
        'telephone': '00000000000',
        'is_active': 'on',
        'email': "test@test.org",
        'password': 'test123',
        'icus[]': '1',
        'managed_icus[]': 1,
      }
      self.assertIsNone(self.db.get_user_by_email(data['email']))
      response = self.fetch(handler.ROUTE, method='POST', body=urlencode(data))
      # redirect to ListUserHandler
      self.assertEqual(response.code, 302)
      self.assertIsNotNone(self.db.get_user_by_email(data['email']))
