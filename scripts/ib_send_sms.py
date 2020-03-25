"""Cron script to send out bed availability requests to all users by SMS."""
from icubam import config
from icubam.db import gsheets
from icubam.messaging import mb_sender

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS

def main(unused_argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode)
  sdb = gsheets.SheetsDB(cfg.TOKEN_LOC, cfg.SHEET_ID)
  sender = mb_sender.MBSender(
    api_key=config.SMS_KEY, originator=cfg.sms.origin
  )

  users = sdb.get_users()
  print(users)
  for row in users.iterrows():
    print(row)
    tel = row[1]["tel"]
    print(tel)
    sender.send_message(tel, "Test")


if __name__ == "__main__":
  main(None)
