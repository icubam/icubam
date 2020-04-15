import tornado.testing
import tornado.web
import tornado.httpserver

from icubam import config
from icubam.backoffice import server
from icubam.backoffice.handlers import bedcounts
from icubam.db import store


class MockConnection:
  def set_close_callback(self, callback):
    pass


class TestListBedCountsHandler(tornado.testing.AsyncTestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    self.server = server.BackOfficeServer(self.config, port=8889)
    self.app = self.server.make_app()
    self.request = tornado.httpserver.HTTPRequest(
      method='GET',
      uri=bedcounts.ListBedCountsHandler.ROUTE,
      headers=None,
      body=None
    )
    self.request.connection = MockConnection()
    self.handler = bedcounts.ListBedCountsHandler(self.app, self.request)
    self.handler.initialize()

    self.admin_id = self.handler.db.add_default_admin()
    rid = self.handler.db.add_region(
      self.admin_id, store.Region(name='myregion')
    )
    self.icuid = self.handler.db.add_icu(
      self.admin_id, store.ICU(name='iuc1', region_id=rid)
    )

  def test_prepare_data(self):
    icu = self.handler.db.get_icu(self.icuid)
    bedcount = store.BedCount(
      icu_id=icu.icu_id, n_covid_occ=12, n_covid_free=4
    )
    self.handler.db.update_bed_count_for_icu(self.admin_id, bedcount)
    icu = self.handler.db.get_icu(self.icuid)
    locale = self.handler.get_user_locale()
    data = self.handler.prepare_data(icu, locale)
    self.assertIsInstance(data, list)
    self.assertGreater(len(data), 0)
    for k in ['key', 'value', 'link']:
      self.assertIn(k, data[0])
