import os
import tornado.web
import logging
import time
from icubam.www.handlers import base


class UploadHandler(base.BaseHandler): #tornado.web.RequestHandler):
  """Accept file uploads over POST."""

  ROUTE = "/upload_csv"
  API_COOKIE = 'api'

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      return

    return self.db.auth_external_client(key)

  def gen_path(self, f_name):
    time_str = time.strftime("%Y-%m-%d-%H:%M:%S")
    return os.path.join(self.upload_path, f"{time_str}-{f_name}")

  def initialize(self, upload_path, config, db_factory):
    self.upload_path = upload_path
    print(db_factory)
    super().initialize(config, db_factory)

  @tornado.web.authenticated
  def post(self):
    file = self.request.files["file"][0]
    file_path = self.gen_path(file["filename"])
    print(self.request)
    try:
      with open(file_path, "wb") as f:
        f.write(file["body"])
      logging.info(f"Received {file_path} from {self.request.remote_ip}.")

    except IOError as e:
      logging.error(f"Failed to write file due to IOError: {e}")
