import datetime
import io
import logging
import os
import tempfile

import pandas as pd
import tornado.web

from icubam.www.handlers import base, home

access_log = logging.getLogger('tornado.access')


def _get_headers(collection, asked_file_type):
  if asked_file_type not in {'csv', 'hdf'}:
    return dict()
  extension = 'csv' if asked_file_type == 'csv' else 'h5'
  datestr = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%M')
  filename = f'{collection}_{datestr}.{extension}'
  content_type = (
    'text/csv' if asked_file_type == 'csv' else 'application/octetstream'
  )
  headers = {
    'Content-Type': content_type,
    'Content-Disposition': f'attachment; filename={filename}'
  }
  return headers


class DBHandler(base.BaseHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, config, db):
    super().initialize(config, db)
    keys = ['users', 'bedcount', 'icus']
    self.get_fns = {k: getattr(self.db, f'get_{k}', None) for k in keys}

  @tornado.web.authenticated
  def get(self, collection):
    get_fn = self.get_fns.get(collection, None)
    if get_fn is None:
      self.redirect(home.HomeHandler.ROUTE)
    hdf = self.get_query_argument('hdf', default=None)
    csv = self.get_query_argument('csv', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    data = get_fn(max_ts=max_ts)
    asked_file_type = None
    if hdf: asked_file_type = 'hdf'
    if csv: asked_file_type = 'csv'
    access_log.debug(f'request on collection {collection}')
    access_log.debug(f'asked file type: {asked_file_type}')
    for k, v in _get_headers(collection, asked_file_type).items():
      self.set_header(k, v)
      access_log.debug(f'setting header {k} = {v}')
    if asked_file_type == 'csv':
      stream = io.StringIO()
      data.to_csv(stream)
      self.write(stream.getvalue())
    elif asked_file_type == 'hdf':
      with tempfile.NamedTemporaryFile() as f:
        tmp_path = f.name
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
      self.write(data.to_html())
