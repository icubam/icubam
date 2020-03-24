import os
import time

from absl.testing import absltest
from sqlite import SQLiteDB


class SQLiteDBTest(absltest.TestCase):
  def test_init(self):
    tmp_folder = self.create_tempdir()
    sqldb = SQLiteDB(os.path.join(tmp_folder.full_path, "test.db"))

  def test_icu_creation(self):
    tmp_folder = self.create_tempdir()
    sqldb = SQLiteDB(os.path.join(tmp_folder.full_path, "test.db"))
    sqldb.add_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
    sqldb.add_icu("ICU2", "dep2", "city2", 3.44, 42.3)

    with self.assertRaises(ValueError):
      sqldb.add_icu("ICU2", "dep3", "city3", 3.44, 42.3)

  def test_user_creation(self):
    tmp_folder = self.create_tempdir()
    sqldb = SQLiteDB(os.path.join(tmp_folder.full_path, "test.db"))
    with self.assertRaises(ValueError):
      sqldb.add_user("ICU1", "Bob", "+33698158092", "Chercheur")
    sqldb.add_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
    sqldb.add_user("ICU1", "Bob", "+33698158092", "Chercheur")
    with self.assertRaises(ValueError):
      sqldb.add_user("ICU1", "Bob", "+33698158092", "Chercheur")
    sqldb.get_users()

  def test_bedcount_update(self):
    tmp_folder = self.create_tempdir()
    sqldb = SQLiteDB(os.path.join(tmp_folder.full_path, "test.db"))

    # Make sure you can't insert without a valid icu_id
    with self.assertRaises(ValueError):
      sqldb.update_bedcount(1, "test", 10, 9, 8, 7, 6, 5)
    sqldb.add_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
    sqldb.add_icu("ICU2", "dep1", "city1", 3.44, 42.3, "0102")

    # Generate some bed updates:
    for i in [1, 2]:
      for j in range(10):
        time.sleep(0.5)
        sqldb.update_bedcount(i, "test", 10, 9, 8, 7, 6, 5)
    bedcount = sqldb.get_bedcount()
    self.assertLen(bedcount, 2)

    # Make sure the returned updates are the most recent
    for i in [1, 2]:
      res = sqldb.execute(
        f"SELECT MAX(update_ts) as max_ts FROM bed_updates WHERE icu_id = {i}"
      )
      max_ts = res.iloc[0]["max_ts"]
      self.assertEqual(
        bedcount[bedcount["icu_id"] == i].iloc[0]["update_ts"], max_ts
      )

if __name__ == "__main__":
  absltest.main()
