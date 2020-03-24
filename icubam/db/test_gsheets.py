from icubam import config
from icubam.db import gsheets
from absl.testing import absltest


class SQLiteDBTest(absltest.TestCase):
  def test_users(self):
    shdb = gsheets.SheetsDB(config.TOKEN_LOC, config.SHEET_ID)
    shdb.get_users()

  def test_icus(self):
    shdb = gsheets.SheetsDB(config.TOKEN_LOC, config.SHEET_ID)
    shdb.get_icus()


if __name__ == "__main__":
  absltest.main()
