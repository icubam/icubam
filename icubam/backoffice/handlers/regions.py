"""Creating/edition of Regions."""
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.db import store


class ListRegionsHandler(base.AdminHandler):
  ROUTE = "/list_regions"

  def prepare_for_table(self, region):
    result = region.to_dict(max_depth=0)
    for key in ['last_modified', 'icu']:
      result.pop(key, None)
    return self.format_list_item(result)

  @tornado.web.authenticated
  def get(self):
    regions = self.db.get_regions()
    data = [self.prepare_for_table(region) for region in regions]
    self.render("list.html",
                data=data,
                objtype='Regions',
                create_route=RegionHandler.ROUTE)


class RegionHandler(base.AdminHandler):
  ROUTE = "/region"

  @tornado.web.authenticated
  def get(self):
    region = self.db.get_region(self.get_query_argument('id', None))
    region = region if region is not None else store.Region()
    self.render("region.html", region=region, error='')

  @tornado.web.authenticated
  def post(self):
    region_id = self.db.get_region(self.get_query_argument('id', None))
    values = self.parse_from_body(store.Region)
    # TODO(olivier): try catch error here.
    if region_id is None:
      self.db.add_region(self.user.user_id, store.Region(**values))
    else:
      self.db.update_region(self.user.user_id, region_id, values)

    return self.redirect(ListRegionsHandler.ROUTE)
