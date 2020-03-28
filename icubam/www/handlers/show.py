import tornado.web
from tornado import escape
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token
from icubam.www.handlers import update


class DataJson(base.BaseHandler):
  ROUTE = '/beds'

  def initialize(self, db):
    self.db = db

  def get_icu_data(self):
    """Get bedcounts and augment it with extra information."""
    df = self.db.get_bedcount() # query data from db
    # insert column at last positon applying 'time_ago' to the column 'update_ts'
    df['since_update'] = df.update_ts.apply(update.time_ago)
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

  def initialize(self, db):
    self.db = db

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    self.render("show.html")
