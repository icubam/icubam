import os
import time

from absl.testing import absltest
from icubam.db import sqlite
import pandas as pd
import sqlalchemy.exc
import tempfile

class SQLiteDBTest(absltest.TestCase):

  def test_init(self):
    with tempfile.TemporaryDirectory() as tmp_folder:
        sqldb = sqlite.SQLiteDB(os.path.join(tmp_folder, "test.db"))

  def test_icu_creation(self):
    with tempfile.TemporaryDirectory() as tmp_folder:
        sqldb = sqlite.SQLiteDB(os.path.join(tmp_folder, "test.db"))
        sqldb.upsert_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
        icus = sqldb.get_icus()
        self.assertEqual(icus[icus["icu_name"] == "ICU1"].iloc[0]["dept"], "dep1")

        sqldb.upsert_icu("ICU2", "dep2", "city2", 3.44, 42.3, active=False)
        icus = sqldb.get_icus()
        self.assertEqual(icus[icus["icu_name"] == "ICU2"].iloc[0]["dept"], "dep2")
        self.assertEqual(
            icus[icus["icu_name"] == "ICU2"].iloc[0]["active"], False)

        sqldb.upsert_icu("ICU1", "dep3", "city3", 3.44, 42.3, "0103")
        icus = sqldb.get_icus()
        self.assertEqual(icus[icus["icu_name"] == "ICU1"].iloc[0]["dept"], "dep3")
        self.assertEqual(icus[icus["icu_name"] == "ICU1"].iloc[0]["telephone"], "0103")
        self.assertEqual(icus[icus["icu_name"] == "ICU1"].iloc[0]["active"], True)
        self.assertEqual(sqldb.get_icu_id_from_name("ICU1"), 1)
        self.assertEqual(sqldb.get_icu_id_from_name("ICU2"), 2)


  def test_user_creation(self):
    with tempfile.TemporaryDirectory() as tmp_folder:
      sqldb = sqlite.SQLiteDB(os.path.join(tmp_folder, "test.db"))

      # Make sure you can't add a user with non-existant ICU
      with self.assertRaises(ValueError):
        sqldb.add_user("ICU1", "Bob", "+33698158092", "Chercheur")

      # Check normal insertion
      sqldb.upsert_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
      sqldb.add_user("ICU1", "Bob", "+33698158092", "Chercheur", "bob@test.org")

      with self.assertRaises(sqlalchemy.exc.IntegrityError):
        sqldb.add_user("ICU1", "Bob", "+33698158092", "Chercheur")

      # No email.
      sqldb.add_user("ICU1", "Alice", "+33612345678", "Docteur")

      users = sqldb.get_users()
      pd.testing.assert_frame_equal(
          users,
          pd.DataFrame({
              "icu_id": [1, 1],
              "icu_name": ["ICU1", "ICU1"],
              "name": ["Bob", "Alice"],
              "telephone": ["+33698158092", "+33612345678"],
              "description": ["Chercheur", "Docteur"],
              "email": ["bob@test.org", "NULL"],
          }))

  def test_bedcount_update(self):
    with tempfile.TemporaryDirectory() as tmp_folder:
        sqldb = sqlite.SQLiteDB(os.path.join(tmp_folder, "test.db"))

        # Make sure you can't insert without a valid icu_id
        with self.assertRaises(ValueError):
          sqldb.update_bedcount(1, "test", 10, 9, 8, 7, 6, 5, 4)
        sqldb.upsert_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
        sqldb.upsert_icu("ICU2", "dep1", "city1", 3.44, 42.3, "0102")

        # Generate some bed updates:
        for i in [1, 2]:
          for j in range(10):
            time.sleep(0.5) # Need to keep a delta of at least 0.5
            sqldb.update_bedcount(i, "test", 10, 9, 8, 7, 6, 5, 4)
        bedcount = sqldb.get_bedcount()
        self.assertLen(bedcount, 2)

        # Make sure the returned updates are the most recent
        for i in [1, 2]:
          res = sqldb.pd_execute(
            f"SELECT MAX(update_ts) as max_ts FROM bed_updates WHERE icu_id = {i}"
          )
          max_ts = res.iloc[0]["max_ts"]
          self.assertEqual(
            bedcount[bedcount["icu_id"] == i].iloc[0]["update_ts"], max_ts
          )


  def test_bedcount_where(self):
    with tempfile.TemporaryDirectory() as tmp_folder:
        sqldb = sqlite.SQLiteDB(os.path.join(tmp_folder, "test.db"))

        sqldb.upsert_icu("ICU1", "dep1", "city1", 3.44, 42.3, "0102")
        sqldb.upsert_icu("ICU2", "dep1", "city1", 3.44, 42.3, "0102")

        # Check that bedcounts can be select by icu_id:
        for i in range(10):
          sqldb.upsert_icu(f"ICU{i}", f"dep{i}", f"city{i}", 3.44, 42.3)
          sqldb.update_bedcount(i+1, "test", 10, 9, 8, 7, 6, 5, 4)

        beds = sqldb.get_bedcount(icu_ids=(1,2,4,7))
        self.assertEqual(len(beds), 4)

        cur_time = int(time.time())
        for i in range(10):
          for j in range(10):
            sqldb.update_bedcount(i+1, "test", 10, 9, 8, 7, 6, 5, 4, update_ts=cur_time + j)

        max_time = sqldb.get_bedcount()['update_ts'].max()
        # import ipdb; ipdb.set_trace()
        new_max_time = sqldb.get_bedcount(max_ts=max_time - 3)['update_ts'].max()
        self.assertEqual(new_max_time, max_time - 4)



if __name__ == "__main__":
  absltest.main()
