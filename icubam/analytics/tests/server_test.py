from io import StringIO

import tornado.testing
import pandas as pd
from icubam import config
from icubam.db import store
from icubam.db.fake import populate_store_fake
from icubam.analytics import server


class TestAnalyticsServer(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG)
    self.server = server.AnalyticsServer(self.config, port=8866)
    self.db = self.server.db_factory.create()
    self.admin_id = self.db.add_default_admin()
    self.icu_id = self.db.add_icu(self.admin_id, store.ICU(name='icu'))
    self.user_id = self.db.add_user_to_icu(
      self.admin_id, self.icu_id,
      store.User(name='user', consent=True, is_active=True)
    )
    self.user = self.db.get_user(self.user_id)
    self.icu = self.db.get_icu(self.icu_id)
    super().setUp()

  def get_app(self):
    populate_store_fake(self.db)
    self.server.dataset.db = self.db
    return self.server.make_app()

  def test_db_all_bedcounts(self):
    route = "/db/all_bedcounts?format=csv"

    def check_response_csv(self, response):
      """Check the the response CSV is well formatted"""
      self.assertEqual(response.code, 200)
      csv = StringIO(response.body.decode('utf-8'))
      df = pd.read_csv(csv)
      self.assertIn('icu_name', df.columns)
      self.assertGreater(df.shape[0], 0)

    # CSV with no preprocessing
    response = self.fetch(route, method="GET")
    check_response_csv(self, response)

    # CSV with preprocessing
    url = f'{route}&preprocess=true'
    response = self.fetch(url, method="GET")
    check_response_csv(self, response)
