"""Runs the webserver."""
from absl import logging
import multiprocessing as mp

from absl import app
from absl import flags

from icubam import config
from icubam.backoffice import server as backoffice_server
from icubam.messaging import server as msg_server
from icubam.www import server as www_server

flags.DEFINE_integer('port', None, 'Port of the application.')
flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string(
  'dotenv_path', config.DEFAULT_DOTENV_PATH,
  'Optionally specifies the .env path.'
)
flags.DEFINE_string('server', 'www', 'File for the db.')
FLAGS = flags.FLAGS


def run_one_server(cls, cfg):
  logging.set_verbosity(logging.INFO)
  cls(cfg, None).run()


def main(argv):
  servers = {
    'www': www_server.WWWServer,
    'message': msg_server.MessageServer,
    'backoffice': backoffice_server.BackOfficeServer,
  }
  service = servers.get(FLAGS.server, None)
  cfg = config.Config(FLAGS.config, env_path=FLAGS.dotenv_path)
  if service is not None:
    service(cfg, FLAGS.port).run()
  elif FLAGS.server == 'all':
    processes = [
      mp.Process(target=run_one_server, args=(cls, cfg))
      for cls in servers.values()
    ]
    for p in processes:
      p.start()


if __name__ == '__main__':
  app.run(main)
