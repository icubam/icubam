"""Creating/edition of ICUs."""
from absl import logging
import json
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import store


class ListICUsHandler(base.BaseHandler):
  ROUTE = "list_icus"

  def prepare_for_table(self, icu):
    result = [{
      'key': 'name',
      'value': icu.name,
      'link': f'{ICUHandler.ROUTE}?id={icu.icu_id}'
    }]
    icu_dict = {}
    icu_dict['city'] = icu.city
    icu_dict['dept'] = icu.dept
    icu_dict['region'] = icu.region.name
    icu_dict['active'] = icu.is_active
    icu_dict['users'] = len(icu.users)
    icu_dict['managers'] = len(icu.managers)
    result.extend(self.format_list_item(icu_dict))
    return result

  @tornado.web.authenticated
  def get(self):
    if self.current_user.is_admin:
      icus = self.db.get_icus()
    else:
      icus = self.db.get_managed_icus(self.current_user.user_id)

    data = [self.prepare_for_table(icu) for icu in icus]
    return self.render_list(
      data=data, objtype='ICUs', create_handler=ICUHandler, upload=True
    )


class ICUHandler(base.BaseHandler):
  ROUTE = "icu"

  def do_render(self, icu, error=False):
    if self.current_user.is_admin:
      regions = self.db.get_regions()
    if not self.current_user.is_admin:
      regions = [e.region for e in self.current_user.managed_icus]
    regions.sort(key=lambda r: r.name)

    depts = sorted(set([i.dept for i in self.db.get_managed_icus()]))
    icu = icu if icu is not None else store.ICU()
    if icu.is_active is None:
      icu.is_active = True
    return self.render(
      "icu.html",
      icu=icu,
      depts=json.dumps(depts),
      regions=regions,
      error=error,
      list_route=ListICUsHandler.ROUTE
    )

  @tornado.web.authenticated
  def get(self):
    icu = self.db.get_icu(self.get_query_argument('id', None))
    return self.do_render(icu)

  @tornado.web.authenticated
  def post(self):
    values = self.parse_from_body(store.ICU)
    values["is_active"] = values.get("is_active", "off") == 'on'
    values['region_id'] = int(values.get('region_id', -1))
    id_key = 'icu_id'
    icu_id = values.pop(id_key, '')
    try:
      if not icu_id:
        icu_id = self.db.add_icu(
          self.current_user.user_id, store.ICU(**values)
        )
      else:
        self.db.update_icu(self.current_user.user_id, icu_id, values)
    except Exception as e:
      logging.error(f'Cannot save ICU: {e}')
      values[id_key] = icu_id
      return self.do_render(store.ICU(**values), error=True)

    return self.redirect(ListICUsHandler.ROUTE)
