"""Runs the webserver."""
from absl import app
from absl import flags
from absl import logging

from icubam import config
from icubam.db import store

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
flags.DEFINE_string('email', None, 'File for the db.')
flags.DEFINE_string('password', None, 'File for the db.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  factory = store.create_store_factory_for_sqlite_db(cfg)
  db = factory.create()
  user_id = db.get_user_by_email(FLAGS.email)
  if user_id is None:
    logging.error(f"No user for email {FLAGS.email}")
    return

  admins = db.get_admins()
  if not admins:
    admin_id = db.add_default_admin()
  else:
    admin_id = admins[0].user_id

  hash = db.get_password_hash(FLAGS.password)
  db.update_user(admin_id, user_id, dict(password_hash=hash))


if __name__ == '__main__':
  app.run(main)
