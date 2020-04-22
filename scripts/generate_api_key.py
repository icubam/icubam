"""This scripts generates an API KEY for external users to access the map."""

from absl import app
from absl import flags
from absl import logging
from icubam import config
from icubam.db import store

flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string(
  'dotenv_path', config.DEFAULT_DOTENV_PATH,
  'Optionally specifies the .env path.'
)
flags.DEFINE_string('name', None, 'Meta data.')
flags.DEFINE_string('email', None, 'Meta data.')
flags.DEFINE_string('telephone', None, 'Meta data.')
FLAGS = flags.FLAGS


def main(argv):
  fields = ['name', 'telephone', 'email']
  values = {k: FLAGS[k].value for k in fields if FLAGS[k].value is not None}
  cfg = config.Config(FLAGS.config, env_path=FLAGS.dotenv_path)
  db_factory = store.create_store_factory_for_sqlite_db(cfg)
  db = db_factory.create()
  users = db.get_admins()
  if users:
    admin_id = users[0].user_id
  else:
    admin_id = db.add_default_admin()

  user_query = store.ExternalClient(**values)
  user = db.get_external_client_by_email(user_query.email)
  if user is None:
    logging.info(
      "New access token: {}".format(
        db.add_external_client(admin_id, user_query)
      )
    )
  else:
    c_id = user.external_client_id
    db.update_external_client(admin_id, c_id, values)
    logging.info(f"Updated client {c_id} with values: {values}")


if __name__ == '__main__':
  app.run(main)
