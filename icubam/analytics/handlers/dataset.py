import io

from absl import logging  # noqa: F401
import tornado.web


class DatasetHandler(tornado.web.RequestHandler):

  ROUTE = '/db/(.*)'

  def initialize(self, dataset):
    super().initialize()
    self.dataset = dataset

  def get(self, collection):
    file_format = self.get_query_argument('format', default=None)
    max_ts = self.get_query_argument('max_ts', default=None)
    should_preprocess = (
      self.get_query_argument('preprocess', default=None) is not None
    )
    df = self.dataset.get(collection, max_ts, should_preprocess)
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
