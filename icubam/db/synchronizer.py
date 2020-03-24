"""Pulls data from the google sheet and adds it to the sqlite DB."""
import gsheets
import sqlite
import logging

class Synchronizer:
  """This will take data from the google sheet and put it into the sqlite DB.

  If the ICU name is already present, or the user telephone is already present,
  then it will *not* get updated.  If there is no existing row then
  a new row with the ICU or user info will get added."""
  def __init__(self, sheets_db, sqlite_db):
    self._shdb = sheets_db
    self._sqldb = sqlite_db

  def sync_icus(self):
    icus = self._shdb.get_icus()
    for row in icus.iterrows():
      icu = row[1]
      try:
        self._sqldb.add_icu(
          icu["icu_name"],
          icu["dept"],
          icu["city"],
          icu["lat"],
          icu["long"],
          icu["telephone"],
        )
        logging.info('Added ICU {}'.format(icu["icu_name"]))
      except ValueError as e:
        logging.error(e)
        continue

  def sync_users(self):
    users = self._shdb.get_users()
    for row in users.iterrows():
      user = row[1]
      try:
        self._sqldb.add_user(
          user["icu_name"],
          user["name"],
          user["tel"],
          user["description"]
        )
        logging.info('Added user {}'.format(user["name"]))
      except ValueError as e:
        logging.error(e)
        continue


if __name__ == "__main__":
  from icubam import config

  shdb = gsheets.SheetsDB(config.TOKEN_LOC, config.SHEET_ID)
  sqldb = sqlite.SQLiteDB(config.SQLITE_DB)
  sync = Synchronizer(shdb, sqldb)
  sync.sync_icus()
  sync.sync_users()
