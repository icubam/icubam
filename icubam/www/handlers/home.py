from absl import logging
import tornado.web

import icubam
from icubam.db import store
from icubam.www.handlers import base
from icubam import map_builder


class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.icu = None

  @tornado.web.authenticated
  def get(self):
    locale = self.get_user_locale()
    builder = map_builder.MapBuilder(self.config, self.db, locale)
    data, center = builder.prepare_jsons(
      None, center_icu=self.icu, level='dept'
    )
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
