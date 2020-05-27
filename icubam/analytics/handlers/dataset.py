from datetime import datetime
import io
import os

from absl import logging  # noqa: F401
import tornado.web
from icubam.db import store, synchronizer
from icubam.www.handlers import base


class DatasetHandler(base.APIKeyProtectedHandler):

  ROUTE = '/db/(.*)'
  API_COOKIE = 'api'
  ACCESS = [
    store.AccessTypes.STATS, store.AccessTypes.ALL, store.AccessTypes.UPLOAD
  ]
  GET_ACCESS = [store.AccessTypes.ALL, store.AccessTypes.STATS]
  POST_ACCESS = [store.AccessTypes.UPLOAD, store.AccessTypes.STATS]

  def initialize(self, config, db_factory, dataset, upload_path):
    super().initialize(config, db_factory)
    self.dataset = dataset
    self.upload_path = upload_path

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

  @tornado.web.authenticated
  def post(self, collection):

    if self.current_user.access_type not in self.POST_ACCESS:
      logging.info(
        f"API called with incorrect access_type: {self.current_user.access_type}."
      )
      self.set_status(403)
      return

    # Send to the correct endpoint:
    if collection == 'bedcounts':
      csvp = synchronizer.CSVPreprocessor(self.db)

      # Get the file object and format request:
      file = self.request.files["file"][0]
      file_format = self.get_query_argument('format', default=None)
      file_name = None
      # Pre-process with the correct method:
      if file_format == 'ror_idf':
        input_buf = io.StringIO(file["body"].decode('utf-8'))
        try:
          csvp.sync_bedcounts_ror_idf(input_buf)
        except Exception as e:
          logging.error(f"Couldn't sync: {e}")
        file_name = 'ror_idf'
      else:
        logging.debug("API called with incorrect file_format: {file_format}.")
        self.set_status(400)
        return

      # Save the file locally just in case:
      time_str = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
      file_path = os.path.join(self.upload_path, f"{time_str}-{file_name}")
      try:
        with open(file_path, "wb") as f:
          f.write(file["body"])
        logging.info(f"Received {file_path} from {self.request.remote_ip}.")
      except IOError as e:
        logging.error(f"Failed to write file due to IOError: {e}")

    # Or 404 if bad endpoint:
    else:
      logging.error(f"DB POST accessed with incorrect endpoint: {collection}.")
      self.set_status(404)
      return
