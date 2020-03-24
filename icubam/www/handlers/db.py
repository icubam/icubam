import tornado.web
from icubam.www.handlers import base


class DBHandler(base.BaseHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, db):
    self.db = db
    keys = ['users', 'bedcount', 'icus']
    self.get_fns = {k: getattr(self.db, f'get_{k}', None) for k in keys}

  def get(self, collection):
    get_fn = self.get_fns.get(collection, None)
    if get_fn is not None:
      self.write(get_fn().to_html())
