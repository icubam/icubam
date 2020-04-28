"""Creating/edition of Regions."""
from absl import logging
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import store


class ListRegionsHandler(base.AdminHandler):
  ROUTE = "list_regions"

  def prepare_for_table(self, region):
    result = [{
      'key': 'name',
      'value': region.name,
      'link': f'{RegionHandler.ROUTE}?id={region.region_id}'
    }]
    region_dict = dict()
    region_dict['icus'] = len(region.icus)
    region_dict['created'] = region.create_date
    result.extend(self.format_list_item(region_dict))
    return result

  @tornado.web.authenticated
  def get(self):
    regions = self.db.get_regions()
    data = [self.prepare_for_table(region) for region in regions]
    return self.render_list(
      data=data, objtype=base.ObjType.REGIONS, create_handler=RegionHandler
    )


class RegionHandler(base.AdminHandler):
  ROUTE = "region"

  @tornado.web.authenticated
  def get(self):
    region = self.db.get_region(self.get_query_argument('id', None))
    self.do_render(region)

  def do_render(self, region):
    region = region if region is not None else store.Region()
    self.render(
      "region.html",
      region=region,
      error=False,
      list_route=ListRegionsHandler.ROUTE
    )

  @tornado.web.authenticated
  def post(self):
    values = self.parse_from_body(store.Region)
    id_key = 'region_id'
    region_id = values.pop(id_key, '')
    try:
      if not region_id:
        region_id = self.db.add_region(
          self.current_user.user_id, store.Region(**values)
        )
      else:
        self.db.update_region(self.current_user.user_id, region_id, values)
    except Exception as e:
      logging.error(f'Cannot save region {e}')
      values[id_key] = region_id
      return self.do_render(store.Region(**values))

    return self.redirect(ListRegionsHandler.ROUTE)
