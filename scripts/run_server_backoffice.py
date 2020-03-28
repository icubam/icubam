"""Runs the webserver."""

from absl import app
from absl import flags

from icubam import config
from icubam.backoffice.server import BackOfficeServer

flags.DEFINE_integer('port', 8889, 'Port of the application.')
flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
flags.DEFINE_string('server', 'www', 'File for the db.')
FLAGS = flags.FLAGS


def main(argv):
  servers = {'www': BackOfficeServer}
  service = servers.get(FLAGS.server, None)
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  if service is not None:
    service(cfg, FLAGS.port).run()


if __name__ == '__main__':
  app.run(main)
