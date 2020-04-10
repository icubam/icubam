"""Populates store with fake data."""
from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db.fake import populate_store_fake

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  store = store_factory.create()

  populate_store_fake(store)


if __name__ == '__main__':
  app.run(main)
