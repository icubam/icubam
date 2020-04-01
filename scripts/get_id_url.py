"""Runs the webserver."""

from absl import app
from absl import flags
from icubam import config
from icubam.www import token
from icubam.db import sqlite

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS

def main(argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  sqldb = sqlite.SQLiteDB(cfg.db.sqlite_path)
  icus = sqldb.get_icus()
  encoder = token.TokenEncoder(cfg)
  for user in sqldb.get_users():
    for icu in user.icus:
      print(icu.name, icu.icu_id)
      print(encoder.encode_icu(icu.name, icu.icu_id))

if __name__ == '__main__':
  app.run(main)
