"""Runs the webserver."""
from absl import app
from absl import flags
import multiprocessing as mp

from icubam import config
from icubam.backoffice import server as backoffice_server
from icubam.messaging import server as msg_server
from icubam.www import server as www_server

flags.DEFINE_integer('port', None, 'Port of the application.')
flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
flags.DEFINE_string('server', 'www', 'File for the db.')
FLAGS = flags.FLAGS


def main(argv):
  servers = {
    'www': www_server.WWWServer,
    'message': msg_server.MessageServer,
    'backoffice': backoffice_server.BackOfficeServer,
  }
  service = servers.get(FLAGS.server, None)
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  if service is not None:
    service(cfg, FLAGS.port).run()
  elif FLAGS.server == 'all':
    processes = [
      mp.Process(target=cls(cfg, None).run) for cls in servers.values()
    ]
    for p in processes:
      p.start()


if __name__ == '__main__':
  app.run(main)
