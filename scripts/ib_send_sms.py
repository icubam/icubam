"""Cron script to send out bed availability requests to all users by SMS."""
from icubam import config
from icubam.db import gsheets
from icubam.messaging import mb_sender

print(config.SHEET_ID)


def main(args):
  sdb = gsheets.SheetsDB(config.TOKEN_LOC, config.SHEET_ID)
  sender = mb_sender.MBSender(
    api_key=config.SMS_KEY, originator=config.SMS_ORIG
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
