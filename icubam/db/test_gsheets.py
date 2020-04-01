from icubam import config
from icubam.db import gsheets
from absl.testing import absltest
import os
import unittest


class GsheetsTest(absltest.TestCase):
  gsheets_tokens_def = all([os.environ.get(key, False)
                           for key in ['SHEET_ID', 'TOKEN_LOC']])

  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml', mode='dev')

  @unittest.skipIf(not gsheets_tokens_def,
                   "SHEET_ID or TOKEN_LOC env variables not set")
  def test_users(self):
    shdb = gsheets.SheetsDB(self.config.TOKEN_LOC, self.config.SHEET_ID)
    shdb.get_users()

  @unittest.skipIf(not gsheets_tokens_def,
                   "SHEET_ID or TOKEN_LOC env variables not set")
  def test_icus(self):
    shdb = gsheets.SheetsDB(self.config.TOKEN_LOC, self.config.SHEET_ID)
    shdb.get_icus()


if __name__ == "__main__":
  absltest.main()
