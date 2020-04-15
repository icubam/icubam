import datetime

from absl import app, flags
from dateutil import tz

import icubam.db.store as db_store
from icubam import config
from icubam.db import synchronizer
from icubam.predicu.data import load_pre_icubam

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_string(
  "pre_icubam_data_path", "pre_icubam_data.csv", "Path to pre-icubam CSV file"
)
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")

FLAGS = flags.FLAGS


def add_pre_icubam_bed_counts(pre_icubam_data_path, csv_synchronizer):
  # load the data using predicu's merging of ICU names
  d = load_pre_icubam(data_path=pre_icubam_data_path)
  # ensure the create_datae is tz aware
  d["create_date"] = d.datetime.dt.tz_localize("Europe/Paris").dt.tz_convert(
    tz=tz.tzutc()
  )
  # Antoine's inputs of 2020-03-18 are already present in the database
  # because Gabriel Dulac Arnold entered them manually
  d = d.loc[d.create_date.dt.date > datetime.date(2020, 3, 18)]
  d = d.loc[d.create_date.dt.date < datetime.date(2020, 3, 25)]
  csv_synchronizer.sync_bed_counts(d[list(synchronizer.BC_COLUMNS)])


def main(args=None):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  store = store_factory.create()
  csv_synchronizer = synchronizer.CSVSynchronizer(store)
  add_pre_icubam_bed_counts(FLAGS.pre_icubam_data_path, csv_synchronizer)


if __name__ == "__main__":
  app.run(main)
