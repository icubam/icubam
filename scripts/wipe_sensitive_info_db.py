"""
Wipes sensitive information from an ICUBAM DB.
Warning: modifies data in-place!
"""

from absl import app
from absl import flags
import click
import sqlite3
import sys

from icubam.db.wipe import wipe_db

flags.DEFINE_boolean("force", False, "Do not prompt user confirmation.")
flags.DEFINE_boolean(
  "keep_beds", False, "Whether to keep bed occupation data."
)
flags.DEFINE_string("filename", None, 'DB file name.')
flags.mark_flag_as_required('filename')
FLAGS = flags.FLAGS


def wipe_db_path(path, keep_beds):
  conn = sqlite3.connect(path)
  wipe_db(conn, keep_beds)


def main(argv):
  if not FLAGS.force:
    if not click.confirm(
      "WARNING: THIS WILL WIPE THE DATABASE IN-PLACE. CONTINUE?", err=True
    ):
      return
  wipe_db_path(FLAGS.filename, FLAGS.keep_beds)


if __name__ == "__main__":
  app.run(main)
