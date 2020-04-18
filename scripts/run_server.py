"""Runs the webserver."""
import functools
import multiprocessing as mp

from absl import app
from absl import flags

from icubam import config
from icubam import utils
from icubam.backoffice import server as backoffice_server
from icubam.messaging import server as msg_server
from icubam.www import server as www_server

flags.DEFINE_integer('port', None, 'Port of the application.')
flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string(
  'dotenv_path', config.DEFAULT_DOTENV_PATH,
  'Optionally specifies the .env path.'
)
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
    # For some reason the cfg object won't pickle, so we pass in the
    # necessary values to rebuild it in the child process:
    processes = [
      mp.Process(
        target=functools.partial(
          utils.run_server,
          cls,
          config_path=FLAGS.config,
          mode=FLAGS.mode,
          env_path=FLAGS.dotenv_path
        )
      ) for cls in servers.values()
    ]
    for p in processes:
      p.start()


if __name__ == '__main__':
  app.run(main)
