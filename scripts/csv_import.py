import csv
import sys
from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db.csv import CSV
from icubam.db.store import Store, StoreFactory, BedCount, ExternalClient, ICU, Region, User

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")

flags.DEFINE_bool(
  "forceUpdate", False, "replace db content with csv if entry already exist."
)
flags.DEFINE_string(
  "icu_csv_path", "resources/icu.csv", "path to csv file containing ICU data"
)
flags.DEFINE_string(
  "user_csv_path", "resources/user.csv",
  "path to csv file containing user data"
)

FLAGS = flags.FLAGS


def main(args=None):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  store = store_factory.create()

  csv = CSV(store)

  with open(FLAGS.icus_csv_path) as icus_f:
    csv.import_icus(icus_f, FLAGS.forceUpdate)
  with open(FLAGS.users_csv_path) as users_f:
    csv.import_users(users_f, FLAGS.forceUpdate)


if __name__ == "__main__":
  app.run(main)
