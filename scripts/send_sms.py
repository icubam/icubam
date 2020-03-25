from absl import app
from absl import flags
from icubam import config
from icubam.messaging import sms_sender

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  ms = sms_send.get_sender(cfg, sms_carrier='TW')
  ms.send_message("33698158092", "test TW")
  ms = sms_send.get_sender(cfg, sms_carrier='NX')
  ms.send_message("33698158092", "test NX")
  ms = sms_send.get_sender(cfg, sms_carrier='MB')
  ms.send_message("33698158092", "test MB")

if __name__ == "__main__":
  app.run(main)
