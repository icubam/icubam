import tempfile
import logging
import datetime
import os

import pandas as pd
import tornado.web

from icubam.www.handlers import base
from icubam.www.handlers import home

access_log = logging.getLogger('tornado.access')

class DBHandler(base.BaseHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, config, db):
    super().initialize(config, db)
    keys = ['users', 'bedcount', 'icus']
    self.get_fns = {k: getattr(self.db, f'get_{k}', None) for k in keys}


  def prepare(self):
    file_name = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%M')
    self.set_header('Content-Type', 'application/octet-stream')
    self.set_header(
      "Content-Disposition", f"attachment; filename=bedcount_{file_name}.h5"
    )

  @tornado.web.authenticated
  def get(self, collection):
    get_fn = self.get_fns.get(collection, None)
    hdf = self.get_query_argument('hdf', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    access_log.debug(f'seen request: {get_fn.__name__}')
    access_log.debug(f'\tcollection = {collection}')
    access_log.debug(f'\thdf = {hdf}')
    access_log.debug(f'\tmax_ts = {max_ts}')
    if get_fn is not None:
      if hdf:
        if collection == 'bedcount':
          with tempfile.NamedTemporaryFile() as f:
            tmp_path = f.name
          data = get_fn(max_ts=max_ts)
          data.to_hdf(
            tmp_path,
            key='data',
            complib='blosc:lz4',
            complevel=9,
          )
          with open(tmp_path, 'rb') as f:
            self.write(f.read())
          os.remove(tmp_path)
        else:
          self.write(get_fn().to_csv())
      else:
        self.write(get_fn().to_html())
    else:
      self.redirect(home.HomeHandler.ROUTE)
