import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.db import store



class DBHandler(base.BaseHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, config, db):
    super().initialize(config, db)
    keys = ['users', 'bed_counts', 'icus', 'regions']
    self.get_fns = {k: getattr(self.db, f'get_{k}', None) for k in keys}

  @tornado.web.authenticated
  def get(self, collection):
    get_fn = self.get_fns.get(collection, None)
    do_csv = self.get_query_argument('csv', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    if get_fn is not None:
      if do_csv:
        if collection == 'get_bedcount':
          self.write(get_fn(max_ts=max_ts).to_csv())
        else:
          self.write(get_fn().to_csv())
      else:
        self.write(store.to_pandas(get_fn()).to_html())
    else:
      self.redirect(home.HomeHandler.ROUTE)
