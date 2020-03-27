import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home


class DBHandler(base.BaseHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, db):
    self.db = db
    keys = ['users', 'bedcount', 'icus']
    self.get_fns = {k: getattr(self.db, f'get_{k}', None) for k in keys}

  def get(self, collection):
    print(collection)
    get_fn = self.get_fns.get(collection, None)
    do_csv = self.get_query_argument('csv', default=None)
    if get_fn is not None:
      if do_csv:
        self.write(get_fn().to_csv())
      else:
        self.write(get_fn().to_html())
    else:
      self.redirect(home.HomeHandler.ROUTE)
