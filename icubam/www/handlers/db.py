from absl import logging
import datetime
import io
import functools
import os
import pandas as pd
import tornado.web
import tempfile
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.db import store


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

  def get_current_user(self):
    return self.request.get_query_argument('API_KEY', None)

  def initialize(self, config, db):
    super().initialize(config, db)
    keys = ['users', 'bed_counts', 'icus', 'regions']
    self.get_fns = {k: getattr(self.db, f'get_{k}', None) for k in keys}

  @tornado.web.authenticated
  def get(self, collection):
    get_fn = self.get_fns.get(collection, None)
    if get_fn is None:
      self.redirect(home.HomeHandler.ROUTE)

    if collection == 'bed_counts':
      get_fn = functools.partial(get_fn, max_ts=max_ts)

    hdf = self.get_query_argument('hdf', default=None)
    csv = self.get_query_argument('csv', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    data = store.to_pandas(get_fn())

    asked_file_type = None
    if hdf: asked_file_type = 'hdf'
    if csv: asked_file_type = 'csv'

    for k, v in _get_headers(collection, asked_file_type).items():
      self.set_header(k, v)

    if asked_file_type == 'csv':
      stream = io.StringIO()
      data.to_csv(stream, index=False)
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
