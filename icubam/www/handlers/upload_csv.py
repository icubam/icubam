import os
import tornado.web
import logging
import time
from icubam.www.handlers import base


class UploadHandler(base.BaseHandler):
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
    # Sanitize the name some:
    f_name = os.path.split(f_name)[1]
    f_name, f_ext = os.path.splitext(f_name)
    # Clean out non-alphanumerics (need to split ext first or we lose the '.'):
    f_name, f_ext = [
      "".join(c
              for c in f_name
              if c.isalnum())[:64]
      for f_name in [f_name, f_ext]
    ]
    return os.path.join(self.upload_path, f"{time_str}-{f_name}.{f_ext}")

  def initialize(self, upload_path, config, db_factory):
    self.upload_path = upload_path
    super().initialize(config, db_factory)

  @tornado.web.authenticated
  def post(self):
    file = self.request.files["file"][0]
    file_path = self.gen_path(file["filename"])

    try:
      with open(file_path, "wb") as f:
        f.write(file["body"])
      logging.info(f"Received {file_path} from {self.request.remote_ip}.")

    except IOError as e:
      logging.error(f"Failed to write file due to IOError: {e}")
