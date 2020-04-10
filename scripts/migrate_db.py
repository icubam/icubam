from absl import app
from absl import flags
from icubam import config
from icubam.db import migrator


flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  mgt = migrator.Migrator(cfg)
  reply = input(
      "!!Are you sure you want to migrate your db!! (y/n)").lower().strip()
  if reply == "y":
    mgt.run()


if __name__ == "__main__":
  app.run(main)
