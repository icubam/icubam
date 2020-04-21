"""Populates store with fake data."""
from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db.fake import populate_store_fake

flags.DEFINE_string("config", config.DEFAULT_CONFIG_PATH, "Config file.")
flags.DEFINE_string("dotenv_path", config.DEFAULT_DOTENV_PATH, "Config file.")
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, env_path=FLAGS.dotenv_path)
  store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
  store = store_factory.create()

  populate_store_fake(store)


if __name__ == '__main__':
  app.run(main)
