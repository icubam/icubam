"""Schedules SMS sending with a given delay, or follow the standard schedule."""

from absl import app
from absl import flags
import tornado.ioloop
from icubam import config
from icubam.messaging import server

flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string(
  'dotenv_path', config.DEFAULT_DOTENV_PATH,
  'Optionally specifies the .env path.'
)
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev', 'staging'], 'Run mode.')
flags.DEFINE_integer('delay', None, 'time in seconds to schedule next batch.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  msg_server = server.MessageServer(cfg)
  msg_server.run(FLAGS.delay)


if __name__ == '__main__':
  app.run(main)
