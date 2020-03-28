import functools
import tornado.web
from tornado import escape
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token
from icubam import time_utils


class DataJson(base.BaseHandler):
  ROUTE = '/beds'

  def get_icu_data(self):
    """Get bedcounts and augment it with extra information."""
    df = self.db.get_bedcount() # query data from db
    # insert column at last positon applying 'time_ago' to the column 'update_ts'
    time_ago_fn = functools.partial(
      time_utils.localwise_time_ago, locale=self.get_user_locale())
    df['since_update'] = df.update_ts.apply(time_ago_fn)
    n_covid_tot = df['n_covid_free'] + df['n_covid_occ']
    # insert column at position 1 of dataframe by pushing columns to the right
    df.insert(1, 'n_covid_tot', n_covid_tot)
    return df

  @tornado.web.authenticated
  def get(self):
    data = self.get_icu_data().to_dict(orient="records")
    self.write({"data": data})


class ShowHandler(base.BaseHandler):
  ROUTE = '/show'

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    self.render("show.html")
