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

flags.DEFINE_boolean(
  "force", False, "Do not prompt user confirmation and do not print query."
)
flags.DEFINE_boolean(
  "keep_beds", False, "Whether to keep bed occupation data."
)
FLAGS = flags.FLAGS

def wipe_db_path(path, keep_beds):
  conn = sqlite3.connect(path)
  wipe_db(conn, keep_beds)


def main(argv):
  if len(argv) < 2:
    print(f"Usage: {argv[0]} DB_PATH")
    sys.exit(-1)

  if not FLAGS.force:
    if not click.confirm(
      "WARNING: THIS WILL WIPE THE DATABASE IN-PLACE. CONTINUE?", err=True
    ):
      sys.exit(0)

  wipe_db_path(argv[1], FLAGS.keep_beds)


if __name__ == "__main__":
  app.run(main)
