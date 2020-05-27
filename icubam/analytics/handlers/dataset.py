import io

from absl import logging  # noqa: F401
from icubam.www.handlers import base


class DatasetHandler(base.APIKeyProtectedHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, config, db_factory, dataset):
    super().initialize(config, db_factory)
    self.dataset = dataset

  @base.authenticated(code=503)
  def get(self, collection):
    file_format = self.get_query_argument('format', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    df = self.dataset.get(collection, max_ts)
    if df is None:
      logging.info("API called with incorrect endpoint: {collection}.")
      self.set_status(404)
      return

    if file_format == 'csv':
      stream = io.StringIO()
      df.to_csv(stream, index=False)
      self.write(stream.getvalue())
    else:
      self.write(df.to_html())
