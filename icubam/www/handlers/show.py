import tornado.web
from tornado import escape
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token
from icubam.www.handlers.update import time_ago


class DataJson(base.BaseHandler):
  ROUTE = '/beds'

  def initialize(self, db):
    self.db = db

  def get_icu_data(self):
    df = self.db.get_bedcount()
    df['since_update'] = df.update_ts.apply(time_ago)
    n_covid_tot = df['n_covid_free'] + df['n_covid_occ']
    df.insert(1, 'n_covid_tot', n_covid_tot)
    return df

  @tornado.web.authenticated
  def get(self):
    data = self.get_icu_data().to_dict(orient="records")
    # icu_id = self.db.get_icu_id_from_name("Troyes")
    # tmp = self.db.get_update_ts(icu_ids=[icu_id])
    #  print(tmp.describe())
    # print(tmp.head())
    self.write({"data": data})


class ShowHandler(base.BaseHandler):
  ROUTE = '/show'

  def initialize(self, db):
    self.db = db

  @tornado.web.authenticated
  async def get(self):
    """Serves the page with a form to be filled by the user."""
    self.render("show.html")
