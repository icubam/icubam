"""Runs the webserver."""
from absl import logging  # noqa
from absl import app
from absl import flags

from icubam import config
from icubam.cli import run_server

flags.DEFINE_integer('port', None, 'Port of the application.')
flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string(
  'dotenv_path', config.DEFAULT_DOTENV_PATH,
  'Optionally specifies the .env path.'
)
flags.DEFINE_string('server', 'www', 'File for the db.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(FLAGS.config, env_path=FLAGS.dotenv_path)
  run_server(cfg, server=FLAGS.server, port=FLAGS.port)


if __name__ == '__main__':
  app.run(main)
