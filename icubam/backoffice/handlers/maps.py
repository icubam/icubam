import tornado.web
import icubam
from icubam import map_builder
from icubam.backoffice.handlers import base


class MapsHandler(base.BaseHandler):
  ROUTE = "map"

  def initialize(self):
    super().initialize()
    self.builder = map_builder.MapBuilder(self.config, self.db)

  @tornado.web.authenticated
  def get(self):
    level = self.get_query_argument('level', 'dept')
    data, center = self.builder.prepare_jsons(None, None, level=level)
    return self.render(
      'map.html',
      API_KEY=self.config.GOOGLE_API_KEY,
      center=center,
      data=data,
      version=icubam.__version__
    )
