import os
import re
import tornado.web
import logging
import time

from icubam.db import store
from icubam.www.handlers import base


def clean_path(f_name):
  # Sanitize the name some:
  f_name = f_name.lower()
  f_name = os.path.normpath(f_name)
  f_name = os.path.split(f_name)[1]
  f_name, f_ext = os.path.splitext(f_name)
  # Clean out non-alphanumerics (need to split ext first or we lose the '.'):
  f_name, f_ext = [re.sub(r'\W+', '', n) for n in [f_name, f_ext]]
  if f_ext == '':
    return f_name
  else:
    return f"{f_name}.{f_ext}"


class UploadHandler(base.APIKeyProtectedHandler):
  """Accept file uploads over POST."""

  ROUTE = "/upload_csv"
  API_COOKIE = 'api'
  ACCESS = [store.AccessTypes.UPLOAD, store.AccessTypes.ALL]

  def initialize(self, upload_path, config, db_factory):
    self.upload_path = upload_path
    super().initialize(config, db_factory)

  @tornado.web.authenticated
  def post(self):
    file = self.request.files["file"][0]
    file_name = clean_path(file["filename"])
    time_str = time.strftime("%Y-%m-%d-%H:%M:%S")
    file_path = os.path.join(self.upload_path, f"{time_str}-{file_name}")
    try:
      with open(file_path, "wb") as f:
        f.write(file["body"])
      logging.info(f"Received {file_path} from {self.request.remote_ip}.")

    except IOError as e:
      logging.error(f"Failed to write file due to IOError: {e}")
