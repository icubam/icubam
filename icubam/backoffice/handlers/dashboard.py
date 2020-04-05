import tornado.escape
import tornado.web

from icubam import time_utils
from icubam.backoffice.handlers import base
from icubam.www import updater
from icubam.db import store


class ListBedCountsHandler(base.BaseHandler):
  ROUTE = '/dashboard'

  def initialize(self):
    super().initialize()
    self.link_fn = updater.Updater(self.config, self.db).get_url

  def prepare_data(self, bed_count) -> list:
    icu =  bed_count.icu
    result = [{
      'key': 'icu',
      'value': icu.name,
      'link': self.link_fn(icu.icu_id, icu.name)
    }]

    bed_count_dict = bed_count.to_dict(max_depth=0)
    locale = self.get_user_locale()
    last = bed_count_dict.pop('last_modified').timestamp()
    for key in ['rowid', 'icu_id', 'message', 'create_date']:
      bed_count_dict.pop(key, None)
    bed_count_dict['since_update'] = time_utils.localewise_time_ago(
      last, locale=locale)
    result.extend(self.format_list_item(bed_count_dict))

    return result

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      bed_counts = self.db.get_latest_bed_counts()
    else:
      bed_counts = self.db.get_visible_bed_counts_for_user(self.user.user_id)

    data = [self.prepare_data(bd) for bd in bed_counts]
    self.render(
        "list.html", data=data, objtype='Bed Counts', create_route=None)
