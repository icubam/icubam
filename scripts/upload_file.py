import os
from absl import app
from absl import flags
import requests

flags.DEFINE_string('file_path', None, 'File upload path.')
flags.DEFINE_string('dest', None, 'Destination URL.')

flags.mark_flag_as_required('file_path')
flags.mark_flag_as_required('dest')

FLAGS = flags.FLAGS


def upload_file(url, file_path):
  print(f"Uploading {file_path} to {url}")
  files = {"file": (os.path.split(file_path)[1], open(file_path, "rb"))}
  print(files)
  r = requests.post(url, files=files)
  print(r)


def main(argv):
  upload_file(FLAGS.dest, FLAGS.file_path)


if __name__ == '__main__':
  app.run(main)
