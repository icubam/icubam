from absl import app
from absl import flags
from icubam import config
from icubam.db import sqlite
from icubam.db import gsheets
from icubam.db import synchronizer


def main(unused_argv):
  shdb = gsheets.SheetsDB(config.TOKEN_LOC, config.SHEET_ID)
  sqldb = sqlite.SQLiteDB(config.SQLITE_DB)
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
