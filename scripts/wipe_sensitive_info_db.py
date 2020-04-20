"""
Wipes sensitive information from an ICUBAM DB.
Warning: modifies data in-place!
"""

from absl import app
from absl import flags
import click
import os
from sqlalchemy import create_engine

from icubam.db.store import StoreFactory
from icubam.db.wipe import wipe_db

flags.DEFINE_boolean("force", False, "Do not prompt user confirmation.")
flags.DEFINE_boolean(
  "keep_beds", False, "Whether to keep bed occupation data."
)
flags.DEFINE_boolean("reset_admin", False, "Reset admin information")
flags.DEFINE_string("admin_email", None, "Admin email (if resetting admins)")
flags.DEFINE_string("admin_pass", None, "Admin password (if resetting admins)")
flags.DEFINE_string("filename", None, 'DB file name.')
flags.mark_flag_as_required('filename')
FLAGS = flags.FLAGS


def wipe_db_path(path, keep_beds, reset_admin, admin_email, admin_pass):
  store_factory = StoreFactory(create_engine("sqlite:///" + path))
  wipe_db(
    store_factory.create(), keep_beds, reset_admin, admin_email, admin_pass
  )


def main(argv):
  if not FLAGS.force:
    if not click.confirm(
      "WARNING: THIS WILL WIPE THE DATABASE IN-PLACE. CONTINUE?", err=True
    ):
      return
  wipe_db_path(
    FLAGS.filename, FLAGS.keep_beds, FLAGS.reset_admin, FLAGS.admin_email,
    os.environ.get("ICUBAM_ADMIN_PASS", FLAGS.admin_pass)
  )


if __name__ == "__main__":
  app.run(main)
