import functools
from typing import Dict, List
import tornado.web
from tornado import escape
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www.handlers import update
from icubam.db import store
from icubam.www import updater
from icubam import time_utils


class DataJson(base.BaseHandler):
  ROUTE = '/beds'

  def initialize(self, config, db):
    super().initialize(config, db)
    self.updater = updater.Updater(self.config, self.db)

  def get_icu_data(self) -> List[Dict]:
    """Get bedcounts and augment it with extra information."""
    locale = self.get_user_locale()
    bedcounts = self.db.get_bed_counts()
    data = []
    for count in bedcounts:
      curr = store.to_dict(count)

      last = count.last_modified
      if last is not None:
        last = last.timestamp()
      curr['since_update'] = time_utils.localewise_time_ago(last, locale=locale)
      curr['update_ts'] = last

      free = 0 if count.n_covid_free is None else count.n_covid_free
      occ = 0 if count.n_covid_occ is None else count.n_covid_occ
      curr['n_covid_tot'] = free + occ
      curr['link'] = self.updater.get_url(count.icu.icu_id, count.icu.name)
      curr['icu_name'] = count.icu.name
      for key in ['last_modified', 'create_date']:
        curr.pop(key, None)

      data.append(curr)
    return data

  @tornado.web.authenticated
  def get(self):
    self.write({"data": self.get_icu_data()})


class ShowHandler(base.BaseHandler):
  ROUTE = '/show'

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some
    extra information."""
    self.render("show.html")
