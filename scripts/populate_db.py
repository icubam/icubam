"""This will populate the database from the google sheet."""
from absl import app
from absl import flags
from icubam import config
from icubam.db import sqlite
from icubam.db import gsheets
from icubam.db import synchronizer

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  shdb = gsheets.SheetsDB(cfg.TOKEN_LOC, cfg.SHEET_ID)
  sqldb = sqlite.SQLiteDB(cfg.db.sqlite_path)
  import_sheet = shdb.get_sheet_as_pd("Import")
  sync = synchronizer.Synchronizer(shdb, sqldb)
  sync.sync_icus()
  sync.sync_users()
  sqldb.execute("DELETE FROM bed_updates")
  for row in import_sheet.iterrows():
    row_info = {
      "icu_name": row[1]["Hopital"],
      "n_covid_occ": row[1]["NbCOVID"],
      "n_covid_free": row[1]["NbLitDispo"],
      "n_ncovid_free": 0,
      "n_covid_deaths": row[1]["NbDeces"],
      "n_covid_healed": row[1]["NbSortieVivant"],
      "n_covid_refused": 0,
      "n_covid_transfered": 0,
    }
    icu_id = sqldb.get_icu_id_from_name(row_info["icu_name"])
    row_info["icu_id"] = icu_id
    print(row_info)
    sqldb.update_bedcount(**row_info)


if __name__ == "__main__":
  reply = (
    str(
      input(
        "!!Make sure you delete the .db file before populating!! (yes i understad)"
      )
    )
    .lower()
    .strip()
  )
  if reply == 'yes i understand':
    app.run(main)
