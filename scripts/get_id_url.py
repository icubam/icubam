"""Runs the webserver."""

from sys import exit
from absl import app
from absl import flags
from icubam import config
from icubam.www import token
from icubam.db import store

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
flags.DEFINE_boolean('all', False, 'Get all ids')

FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  sqldb_factory = store.create_store_factory_for_sqlite_db(cfg)
  sqldb = sqldb_factory.create()
  encoder = token.TokenEncoder(cfg)
  for user in sqldb.get_users():
    for icu in user.icus:
      print(encoder.encode_icu(icu.name, icu.icu_id))
      if not FLAGS.all:
        exit()


if __name__ == '__main__':
  app.run(main)
