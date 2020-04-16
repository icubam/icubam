from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db import synchronizer

flags.DEFINE_string("config", config.DEFAULT_CONFIG_PATH, "Config file.")
flags.DEFINE_string("dotenv_path", config.DEFAULT_DOTENV_PATH, "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")

flags.DEFINE_bool(
  "force_update", False,
  "Allow in-place modifications to already present elements."
)

flags.DEFINE_string("icus_csv", None, "Path to csv file containing ICU data.")
flags.DEFINE_string(
  "users_csv", None, "Path to csv file containing user data."
)

FLAGS = flags.FLAGS


def main(args=None):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  store = store_factory.create()
  csv = synchronizer.CSVSynchcronizer(store)

  if FLAGS.icus_csv:
    print(f"Loading ICU CSV from: {FLAGS.icus_csv}")
    with open(FLAGS.icus_csv) as icus_f:
      csv.sync_icus_from_csv(icus_f, FLAGS.force_update)

  if FLAGS.users_csv:
    print(f"Loading user CSV from: {FLAGS.users_csv}")
    with open(FLAGS.users_csv) as users_f:
      csv.sync_users_from_csv(users_f, FLAGS.force_update)


if __name__ == "__main__":
  app.run(main)
