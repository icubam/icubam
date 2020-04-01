"""This scripts generates an API KEY for external users to access the map."""

from absl import app
from absl import flags
from absl import logging
from icubam import config
from icubam.db import store


flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
flags.DEFINE_string('name', None, 'Meta data.')
flags.DEFINE_string('email', None, 'Meta data.')
flags.DEFINE_string('telephone', None, 'Meta data.')
FLAGS = flags.FLAGS


def main(argv):
  fields = ['name', 'telephone', 'email']
  values = {k: FLAGS[k].value for k in fields if FLAGS[k].value is not None}
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  db = store.create_store_for_sqlite_db(cfg)
  users = db.get_admins()
  if users:
    admin_id = users[0].user_id
  else:
    admin_id = db.add_default_admin()

  user_query = store.ExternalClient(**values)
  user = db.get_external_client_by_email(user_query.email)
  if user is None:
    logging.info("New access token: {}".format(
      db.add_external_client(admin_id, user_query)))
  else:
    c_id = user.external_client_id
    db.update_external_client(admin_id, c_id, values)
    logging.info(f"Updated client {c_id} with values: {values}")


if __name__ == '__main__':
  app.run(main)
