"""Runs the webserver."""

from absl import app
from absl import flags
import tornado
from icubam import config
from icubam.www import server as www_server
from icubam.messaging import server as msg_server


flags.DEFINE_integer('port', 8888, 'Port of the application.')
flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
flags.DEFINE_string('server', 'www', 'File for the db.')
FLAGS = flags.FLAGS


def main(argv):
  servers = {'www': www_server.WWWServer, 'message': msg_server.MessageServer}
  service = servers.get(FLAGS.server, None)
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  if service is not None:
    service(cfg, FLAGS.port).run()


if __name__ == '__main__':
  app.run(main)
