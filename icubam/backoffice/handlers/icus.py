"""Creating/edition of ICUs."""
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import store


class ListICUsHandler(base.BaseHandler):
  ROUTE = "/list_icus"

  def prepare_for_table(self, icu):
    result = icu.to_dict(max_depth=1)
    for key in ['users', 'bed_counts', 'managers', 'lat', 'lng', 'create_date']:
      result.pop(key, None)
    result['region'] = result.pop('region', {}).get('name', '-')
    return result

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      icus = self.db.get_icus()
    else:
      icus = self.db.get_managed_icus(self.user.user_id)

    data = [self.prepare_for_table(icu) for icu in icus]
    columns = [] if not data else list(data[0].keys())
    self.render(
      "list.html", data=data, columns=columns, objtype='ICUs',
      create_route=ICUHandler.ROUTE)


class ICUHandler(base.BaseHandler):
  ROUTE = "/icu"

  @tornado.web.authenticated
  def get(self):
    icu = self.db.get_icu(self.get_query_argument('id', None))
    icu = icu if icu is not None else store.ICU()
    if icu.is_active is None:
      icu.is_active = True

    if self.user.is_admin:
      regions = self.db.get_regions()
    if not self.user.is_admin:
      regions = [e.region for e in self.user.managed_icus]
    regions.sort(key=lambda r: r.name)
    self.render("icu.html", icu=icu, regions=regions, error='')

  @tornado.web.authenticated
  def post(self):
    icu_id = self.db.get_icu(self.get_query_argument('id', None))
    values = self.parse_from_body(store.ICU)
    values["is_active"] = bool(values["is_active"])
    if icu_id is None:
      self.db.add_icu(self.user.user_id, store.ICU(**values))
    else:
      self.db.update_icu(self.user.user_id, icu_id, values)

    return self.redirect(ListICUsHandler.ROUTE)
