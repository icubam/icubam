import functools
import tornado.web
from tornado import escape
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www.handlers import update
from icubam.www import updater
from icubam import time_utils


class DataJson(base.BaseHandler):
  ROUTE = '/beds'

  def initialize(self, config, db):
    super().initialize(config, db)
    self.updater = updater.Updater(self.config, self.db)

  def get_icu_data(self):
    """Get bedcounts and augment it with extra information."""
    df = self.db.get_bedcount() # query data from db
    time_ago_fn = functools.partial(
      time_utils.localewise_time_ago, locale=self.get_user_locale())
    df['since_update'] = df.update_ts.apply(time_ago_fn)
    n_covid_tot = df['n_covid_free'] + df['n_covid_occ']
    # Inserts a column at last position applying 'time_ago' to the column
    # 'update_ts'
    df.insert(1, 'n_covid_tot', n_covid_tot)
    return df

  @tornado.web.authenticated
  def get(self):
    data = self.get_icu_data().to_dict(orient="records")
    for v in data:
      v['link'] = self.updater.get_url(v['icu_id'], v['icu_name'])
    self.write({"data": data})


class ShowHandler(base.BaseHandler):
  ROUTE = '/show'

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    self.render("show.html")
