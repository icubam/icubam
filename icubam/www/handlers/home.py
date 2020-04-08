from absl import logging
import json
import tornado.web

import icubam
from icubam.www.handlers import base
from icubam.www import token
from icubam import map_builder


class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.token_encoder = token.TokenEncoder(self.config)
    self.builder = map_builder.MapBuilder(config, self.db)

  @tornado.web.authenticated
  def get(self):
    icu_data = self.token_encoder.decode(self.get_secure_cookie(self.COOKIE))
    if icu_data is None:
      logging.error('Cookie cannot be decoded.')
      return None

    icu = self.db.get_icu(icu_data['icu_id'])
    if icu is None:
      logging.error('No such ICU {}'.format(icu_data['icu_id']))
      return None

    data, center = self.builder.prepare_json(None, center_icu=icu, level='dept')
    return self.render('index.html',
                       API_KEY=self.config.GOOGLE_API_KEY,
                       center=json.dumps(center),
                       data=json.dumps(data),
                       version=icubam.__version__)


class MapByAPIHandler(HomeHandler):
  """Same as HomeHandler but accessed with an API KEY"""

  ROUTE = '/map'

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      return

    return self.db.auth_external_client(key)
