import tornado.escape
import tornado.web

from icubam import time_utils
from icubam.backoffice.handlers import base
from icubam.www import updater
from icubam.db import store


class ListBedCountsHandler(base.BaseHandler):
  ROUTE = 'dashboard'

  def initialize(self):
    super().initialize()
    self.link_fn = updater.Updater(self.config, self.db).get_url


  def make_link(self, icu):
    return {
      'key': 'icu (update link)',
      'value': icu.name,
      'link': self.link_fn(icu.icu_id, icu.name)
    }

  def prepare_data(self, bed_count) -> list:
    result = []
    if bed_count.icu is not None:
      result = [self.make_link(bed_count.icu)]

    bed_count_dict = bed_count.to_dict(max_depth=0)
    locale = self.get_user_locale()
    last = bed_count_dict.pop('last_modified', None)
    last = None if last is None else last.timestamp()
    for key in ['rowid', 'icu_id', 'message', 'create_date', 'icu']:
      bed_count_dict.pop(key, None)
    bed_count_dict['since_update'] = time_utils.localewise_time_ago(
      last, locale=locale)
    result.extend(self.format_list_item(bed_count_dict))
    return result

  def get_empty_icus(self):
    icus = self.db.get_managed_icus(self.user.user_id)
    empty_icus = [i for i in icus if not i.bed_counts]
    result = []
    for icu in empty_icus:
      curr = self.prepare_data(store.BedCount())
      curr.insert(0, self.make_link(icu))
      result.append(curr)
    return result

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      bed_counts = self.db.get_latest_bed_counts()
    else:
      bed_counts = self.db.get_visible_bed_counts_for_user(self.user.user_id)

    data = [self.prepare_data(bd) for bd in bed_counts]
    data.extend(self.get_empty_icus())
    return self.render_list(
      data=data, objtype='Bed Counts', create_handler=None)
