from absl import logging
import functools
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
    do_csv = self.get_query_argument('csv', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    get_fn = self.get_fns.get(collection, None)
    if collection == 'bed_counts':
      get_fn = functools.partial(get_fn, max_ts=max_ts)

    if get_fn is None:
      logging.info(f'no such db {collection}')
      self.redirect(home.HomeHandler.ROUTE)

    data = store.to_pandas(get_fn())
    if do_csv:
      self.write(data.to_csv())
    else:
      self.write(data.to_html())
