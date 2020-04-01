"""Runs the webserver."""

from absl import app
from absl import flags
from icubam import config
from icubam.www import token
from icubam.db import store

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS

def main(argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  sqldb = store.create_store_for_sqlite_db(cfg)
  encoder = token.TokenEncoder(cfg)
  for user in sqldb.get_users():
    for icu in user.icus:
      print(icu.name, icu.icu_id)
      print(encoder.encode_icu(icu.name, icu.icu_id))

if __name__ == '__main__':
  app.run(main)
