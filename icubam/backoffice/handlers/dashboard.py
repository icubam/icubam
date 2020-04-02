import tornado.escape
import tornado.web

from icubam import time_utils
from icubam.backoffice.handlers import base
from icubam.www import updater
from icubam.db import store


class ListBedCountsHandler(base.BaseHandler):
  ROUTE = '/dashboard'

  def initialize(self, config, db):
    super().initialize(config, db)
    self.link_fn = updater.Updater(config, db).get_url

  def prepare_data(self, bed_count) -> dict:
    icu =  bed_count.icu
    result = {'icu': icu.name}
    result.update(bed_count.to_dict(max_depth=0))
    locale = self.get_user_locale()
    last = result.pop('last_modified').timestamp()
    for key in ['rowid', 'icu_id', 'message', 'create_date']:
      result.pop(key, None)
    result['since_update'] = time_utils.localewise_time_ago(last, locale=locale)
    # TODO(olivier): put the links back
    # result['link'] = tornado.escape.linkify(
    #   self.link_fn(icu.icu_id, icu.name), shorten=True)

    return result

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      bed_counts = self.db.get_bed_counts()
    else:
      bed_counts = self.db.get_visible_bed_counts_for_user(self.user.user_id)

    data = [self.prepare_data(bd) for bd in bed_counts]
    columns = [] if not data else list(data[0].keys())
    self.render(
        "list.html", data=data, columns=columns, objtype='Bed Counts',
        create_route=None)
