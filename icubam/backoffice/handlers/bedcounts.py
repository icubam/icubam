import tornado.escape
import tornado.web

from icubam import time_utils
from icubam.backoffice.handlers import base
from icubam.www import updater
from icubam.db import store


class ListBedCountsHandler(base.BaseHandler):
  ROUTE = 'bedcounts'

  def initialize(self):
    super().initialize()
    self.link_fn = updater.Updater(self.config, self.db).get_url

  def prepare_data(self, icu) -> list:
    link = {'key': 'icu (update link)', 'value': icu.name}
    link['link'] = self.link_fn(icu.users[0], icu) if icu.users else '-'
    result = [link]

    bed_count = icu.bed_counts[-1] if icu.bed_counts else store.BedCount()
    bed_count_dict = bed_count.to_dict(max_depth=0)
    locale = self.get_user_locale()
    last = bed_count_dict.pop('create_date', None)
    last = None if last is None else last.timestamp()
    to_pop = [
      'rowid', 'icu_id', 'message', 'create_date', 'last_modified', 'icu'
    ]
    for key in to_pop:
      bed_count_dict.pop(key, None)
    result.extend(self.format_list_item(bed_count_dict))

    display_date = time_utils.localewise_time_ago(last, locale=locale)
    stale = time_utils.is_stale(
      last, days_threshold=self.config.server.num_days_for_stale
    )
    sort_date = last
    result.append({
      'key': 'since_update',
      'value': display_date,
      'warning': stale,
      'sort_value': sort_date,
      'link': False,
    })
    return result

  @tornado.web.authenticated
  def get(self):
    icus = self.db.get_managed_icus(self.user.user_id)
    data = [self.prepare_data(icu) for icu in icus if icu.is_active]
    return self.render_list(
      data=data, objtype='Bed Counts', create_handler=None
    )
