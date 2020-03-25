from absl import app
from absl import flags
from icubam import config
from icubam.db import sqlite
from icubam.db import gsheets
from icubam.db import synchronizer

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAG.config, mode=FLAGS.mode)
  shdb = gsheets.SheetsDB(cfg.TOKEN_LOC, cfg.SHEET_ID)
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
