from absl import app
from absl import flags
from icubam import config
from icubam.db import sqlite
from icubam.db import gsheets
from icubam.db import synchronizer

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_string("sqldb", None, "SQL DB file")
FLAGS = flags.FLAGS

SOURCE_ICUS = ("NHC-CCV", "NHC-USIC", "NHC-Chir")
NEW_ICU_NAME = "NHC-ChirC"

def main(arv):
  cfg = config.Config(FLAGS.config, mode="dev", env_path=FLAGS.dotenv_path)

  sqldb = sqlite.SQLiteDB(FLAGS.sqldb)
  # Get to-be-removed ICU IDs
  icu_ids = []
  for icu_name in SOURCE_ICUS:
    icu_ids.append(sqldb.get_icu_id_from_name(icu_name))

  # Combine ICU entries into one new one, keep same metadata
  icus = sqldb.get_icus()
  icu_row = icus[icus["icu_name"] == SOURCE_ICUS[0]].iloc[0].copy()
  icu_row["icu_name"] = NEW_ICU_NAME
  del icu_row["icu_id"]
  icu_row.to_dict()
  try:
    icu_id = sqldb.get_icu_id_from_name(NEW_ICU_NAME)
  except ValueError:
    pass
  else:
    assert icu_id == 0, "ICU Already present in DB"
  sqldb.upsert_icu(**icu_row.to_dict())
  icu_id = sqldb.get_icu_id_from_name(NEW_ICU_NAME)
  print(f"New ICU ID for {NEW_ICU_NAME}: {icu_id}.")

  # Now accumulate the statistics into a new bedcount entry:
  new_row = sqldb.get_bedcount(icu_ids=icu_ids).sum()
  new_row["icu_name"] = NEW_ICU_NAME
  icu_id = sqldb.get_icu_id_from_name(NEW_ICU_NAME)
  new_row["icu_id"] = icu_id
  del new_row["update_ts"]
  del new_row["message"]
  sqldb.update_bedcount(**new_row.to_dict())

  # Remove entries associated to the old ICUs
  icu_ids = tuple([sqldb.get_icu_id_from_name(name) for name in SOURCE_ICUS])
  query = f"DELETE FROM bed_updates WHERE icu_id IN {icu_ids}"
  print(query)
  sqldb.execute(query)


if __name__ == "__main__":
  app.run(main)
