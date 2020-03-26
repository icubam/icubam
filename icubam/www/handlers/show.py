import tornado.web

from icubam.www.handlers import base


class DataJson(base.BaseHandler):
  ROUTE = '/beds'

  def initialize(self, db):
    self.db = db

  def get_icu_data(self):
    df = self.db.get_bedcount()
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
  def get(self):
    """Serves the page beds"""
    self.render("show.html")
