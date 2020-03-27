import os
import tornado.web
import logging
import time
from icubam.www.handlers import base
from icubam.www.handlers import home


class UploadHandler(tornado.web.RequestHandler):
  """Accept file uploads over POST."""

  ROUTE = "/upload_csv"

  def gen_path(self, f_name):
    time_str = time.strftime("%Y-%m-%d-%H:%M:%S")
    return os.path.join(self.upload_path, f"{time_str}-{f_name}")

  def initialize(self, upload_path):
    self.upload_path = upload_path

  def post(self):
    file = self.request.files["file"][0]
    file_path = self.gen_path(file["filename"])

    try:
      with open(file_path, "wb") as f:
        f.write(file["body"])
      logging.info(f"Received {file_path} from {self.request.remote_ip}.")

    except IOError as e:
      logging.error(f"Failed to write file due to IOError: {e}")
