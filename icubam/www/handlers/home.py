import os.path
import tornado.web

import icubam
from icubam.db import store
from icubam.www.handlers import base
from icubam import map_builder


class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.icu = None  # should be overwritten by the authentication

  def get_disclaimer_url(self):
    """To show a disclaimer link if defined in configuration."""
    if self.config.server.has_key('disclaimer'):
      path = self.config.server.disclaimer
      if path is not None and os.path.exists(path):
        return "<a href='{}disclaimer'>disclaimer</a>".format(
          self.config.server.base_url
        )
    return ""

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
      version=icubam.__version__,
      disclaimer_url=self.get_disclaimer_url()
    )


class MapByAPIHandler(base.APIKeyProtectedHandler):
  """Same as HomeHandler but accessed with an API KEY"""

  ROUTE = '/map'
  ACCESS = [store.AccessTypes.MAP, store.AccessTypes.ALL]

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.regions = None

  def get_disclaimer_url(self):
    if self.config.server.has_key('disclaimer'):
      path = self.config.server.disclaimer
      if path is not None and os.path.exists(path):
        return "<a href='{}disclaimer'>disclaimer</a>".format(
          self.config.server.base_url
        )
    return ""

  @base.authenticated(code=503)
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
      version=icubam.__version__,
      disclaimer_url=self.get_disclaimer_url()
    )
