import pandas as pd
from absl import app, flags
from dateutil import tz
import icubam.db.store as db_store
from icubam import config
from icubam.db import synchronizer
from icubam.predicu.data import load_pre_icubam_data

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_string(
  "pre_icubam_data_path", "pre_icubam_data.csv", "Path to pre-icubam CSV file"
)
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")

FLAGS = flags.FLAGS


def add_pre_icubam_bed_counts(pre_icubam_data_path, csv_synchronizer):
  d = load_pre_icubam_data(data_path=pre_icubam_data_path)
  d["create_date"] = d.datetime.dt.tz_localize("Europe/Paris")
  # import ipdb; ipdb.set_trace()
  d["create_date"] = d["create_date"].dt.tz_convert(tz.tzutc())
  csv_synchronizer.sync_bed_counts(d[list(synchronizer.BC_COLUMNS)])


def main(args=None):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  store = store_factory.create()
  csv_synchronizer = synchronizer.CSVSynchcronizer(store)
  add_pre_icubam_bed_counts(FLAGS.pre_icubam_data_path, csv_synchronizer)


if __name__ == "__main__":
  app.run(main)
