from absl import logging
import tornado.web

import icubam
from icubam.db import store
from icubam.www.handlers import base
from icubam.www import token
from icubam import map_builder


class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.token_encoder = token.TokenEncoder(self.config)

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

    locale = self.get_user_locale()
    builder = map_builder.MapBuilder(self.config, self.db, locale)
    data, center = builder.prepare_jsons(None, center_icu=icu, level='dept')
    return self.render(
      'index.html',
      API_KEY=self.config.GOOGLE_API_KEY,
      center=center,
      data=data,
      version=icubam.__version__
    )


class MapByAPIHandler(base.APIKeyProtectedHandler):
  """Same as HomeHandler but accessed with an API KEY"""

  ROUTE = '/map'
  ACCESS = [store.AccessTypes.MAP, store.AccessTypes.ALL]

  @tornado.web.authenticated
  def get(self):
    locale = self.get_user_locale()
    builder = map_builder.MapBuilder(self.config, self.db, locale)
    regions = [r.region_id for r in self.regions] if self.regions else None
    data, center = builder.prepare_jsons(
      None, center_icu=None, regions=regions, level='dept'
    )
    return self.render(
      'index.html',
      API_KEY=self.config.GOOGLE_API_KEY,
      center=center,
      data=data,
      version=icubam.__version__
    )
