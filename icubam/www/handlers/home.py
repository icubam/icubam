from absl import logging
import collections
import json
import tornado.web
from typing import List, Dict
import icubam
from icubam.www.handlers import base
from icubam.www import token
from icubam import map_builder



class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.builder = map_builder.MapBuilder(
      config, db_factory, 'www/templates/index.html')
    self.token_encoder = token.TokenEncoder(self.config)
    self.popup_template = loader.load(self.POPUP_TEMPLATE)

  def center_map(self):
    icu_data = self.token_encoder.decode(self.get_secure_cookie(self.COOKIE))
    if icu_data is None:
      logging.error('Cookie cannot be decoded.')
      return None

    icu = self.icus.get(icu_data['icu_id'], None)
    if icu is None:
      logging.error('No such ICU {}'.format(icu_data['icu_id']))
      return None

    return {'lat': icu.lat, 'lng': icu.long}

  @tornado.web.authenticated
  def get(self):
    icu_data = self.token_encoder.decode(self.get_secure_cookie(self.COOKIE))
    if icu_data is None:
      logging.error('Cookie cannot be decoded.')
      return None

    icu = self.db.get_icu(icu_data['icu_id'], None)
    if icu is None:
      logging.error('No such ICU {}'.format(icu_data['icu_id']))
      return None

    html = self.builder.to_html(None, center_icu=icu, level='dept')
    return self.write(html)

class MapByAPIHandler(HomeHandler):
  """Same as HomeHandler but accessed with an API KEY"""

  ROUTE = '/map'

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      return

    return self.db.auth_external_client(key)
