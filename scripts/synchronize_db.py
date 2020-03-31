from absl import app
from absl import flags
from icubam import config
from icubam.db import sqlite
from icubam.db import store
from icubam.db import gsheets
from icubam.db import synchronizer

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")
flags.DEFINE_bool('newdb', True, 'Old sqliteDB or new Store.')
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  shdb = gsheets.SheetsDB(cfg.TOKEN_LOC, cfg.SHEET_ID)
  if FLAGS.newdb:
    sqldb = store.create_store_for_sqlite_db(cfg)
    sync = synchronizer.StoreSynchronizer(shdb, sqldb)
  else:
    sqldb = sqlite.SQLiteDB(cfg.db.sqlite_path)
    sync = synchronizer.Synchronizer(shdb, sqldb)
  reply = (
    str(
      input(
        "!!Are you sure you want to sync, this will drop all users!! (duh/nay)"
      )
    )
    .lower()
    .strip()
  )
  if reply == "duh":
    sync.sync_icus()
    sync.sync_users()


if __name__ == "__main__":
  app.run(main)
