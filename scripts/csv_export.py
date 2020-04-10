from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db import synchronizer

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")

flags.DEFINE_string("output", None, "Path for export.")

FLAGS = flags.FLAGS


def main(args=None):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  db = store_factory.create()

  csv = synchronizer.CSVSynchcronizer(db)

  out_buf = csv.export_icus()
  if FLAGS.output:
    with open(FLAGS.output, 'w') as f_out:
      f_out.write(out_buf)
  else:
    print(out_buf)


if __name__ == "__main__":
  app.run(main)
