from absl import app
from absl import flags
from absl import logging
from icubam import config
from icubam.messaging import sms_sender

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_string('phone', None, 'The number to send the sms to.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(
    FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path
  )
  if FLAGS.phone is not None:
    for sms_carrier in ['TW', 'NX', 'MB']:
      ms = sms_sender.get(cfg, sms_carrier=sms_carrier)
      ms.send(FLAGS.phone, f"Test from  {sms_carrier}")
  else:
    logging.error('Specify a phone number.')


if __name__ == "__main__":
  app.run(main)
