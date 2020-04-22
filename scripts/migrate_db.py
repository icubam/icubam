from absl import app
from absl import flags
from icubam import config
from icubam.db import migrator
import click

flags.DEFINE_string("config", config.DEFAULT_CONFIG_PATH, "Config file.")
flags.DEFINE_string("dotenv_path", config.DEFAULT_DOTENV_PATH, "Config file.")
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, env_path=FLAGS.dotenv_path)
  mgt = migrator.Migrator(cfg)
  if not click.confirm(
    "WARNING: THIS WILL UPDATE THE DATABASE IN-PLACE. CONTINUE?", err=True
  ):
    return
  else:
    mgt.run()


if __name__ == "__main__":
  app.run(main)
