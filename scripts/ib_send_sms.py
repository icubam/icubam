"""Cron script to send out bed availability requests to all users by SMS."""
from icubam import config
from icubam.db import gsheets
from icubam.messaging import mb_sender

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_string('dotenv_path', None, 'Optionally specifies the .env path.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
  sdb = gsheets.SheetsDB(cfg.TOKEN_LOC, cfg.SHEET_ID)
  sender = mb_sender.MBSender(cfg)

  users = sdb.get_users()
  print(users)
  for row in users.iterrows():
    print(row)
    tel = row[1]["tel"]
    print(tel)
    sender.send(tel, "Test")


if __name__ == "__main__":
  main(None)
