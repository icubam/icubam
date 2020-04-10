import os
import time
import tempfile
from absl.testing import absltest
from icubam.db import store, synchronizer
import sqlalchemy as sqla


class CSVTest(absltest.TestCase):
  def setUp(self):
    store_factory = store.StoreFactory(
      sqla.create_engine("sqlite:///:memory:", echo=True)
    )
    self.db = store_factory.create()
    self.csv = synchronizer.CSVSynchcronizer(self.db)

  def test_import_icus(self):
    # Import icu.csv, contain 3 ICUs:
    with open("resources/test/icu.csv") as csv_f:
      self.csv.sync_icus_from_csv(csv_f, False)
    n_icu = len(self.db.get_icus())
    self.assertEqual(n_icu, 3, f"3 ICUs should be on db, got {n_icu}.")
    phone1 = self.db.get_icu_by_name("hopital1").telephone

    # Import icu2.csv, contains 4 ICUs: one new and 3 updates.
    with open("resources/test/icu2.csv") as csv_f:
      self.csv.sync_icus_from_csv(csv_f, False)

    n_icu = len(self.db.get_icus())
    self.assertEqual(n_icu, 4, "4 ICUs should be on db, got {n_icu}.")
    new_phone = self.db.get_icu_by_name("hopital1").telephone
    self.assertEqual(
      phone1, new_phone,
      "ICU data should not have been updated with force_update=False."
    )

    # Import icu2.csv again but with forceUpdate enabled.
    with open("resources/test/icu2.csv") as csv_f:
      self.csv.sync_icus_from_csv(csv_f, True)

    n_icu = len(self.db.get_icus())
    self.assertEqual(n_icu, 4, "4 ICUs should be on db, got {n_icu}.")
    new_phone = self.db.get_icu_by_name("hopital1").telephone
    self.assertNotEqual(
      phone1, new_phone,
      "ICU data should have been updated with force_update=True."
    )

  def test_import_users(self):
    with open("resources/test/icu2.csv") as csv_f:
      self.csv.sync_icus_from_csv(csv_f, False)
    with open("resources/test/user.csv") as csv_f:
      self.csv.sync_users_from_csv(csv_f, False)

    n_user = len(self.db.get_users())
    self.assertEqual(
      n_user, 4, f"4 users should be on db(3 imported + admin), got {n_user}"
    )
    desc1 = self.db.get_user_by_phone("111").description

    # user2.csv contains one more user, registers an existing user to a new icu
    # and updates their description
    with open("resources/test/user2.csv") as csv_f:
      self.csv.sync_users_from_csv(csv_f, True)

    n_user = len(self.db.get_users())
    self.assertEqual(
      n_user, 5, f"5 users should be in DB (4 imported + admin), got {n_user}."
    )
    desc2 = self.db.get_user_by_phone("111").description

    self.assertLen(self.db.get_user_by_phone("333").icus, 2, "This user should be registered for 2 ICUs.")

    n_user = len(self.db.get_users())
    self.assertEqual(
      n_user, 5, f"5 users should be in DB (4 imported + admin), got {n_user}."
    )
    desc3 = self.db.get_user_by_phone("111").description
    self.assertNotEqual(desc1, desc3, "User desc. should have been updated.")

  def test_export_icus(self):
    with open("resources/test/icu2.csv") as csv_f:
      self.csv.sync_icus_from_csv(csv_f, False)

    test_dir = tempfile.mkdtemp()
    str_buf = self.csv.export_icus()
  #   assert sum(
  #     1 for line in open(test_dir + "/exported_icu.csv")
  #   ) == 5, "exported file should have the same line number as imported file"
  #   assert filecmp.cmp(
  #     "resources/test/icu2.csv", test_dir + "/exported_icu.csv", shallow=True
  #   ), "exported file should be the same as imported file"

  # def test_export_users(self):
  #   self.csv.import_icus(self.admin_id, "resources/test/icu2.csv", False)
  #   self.csv.import_users(self.admin_id, "resources/test/user2.csv", False)

  #   test_dir = tempfile.mkdtemp()
  #   self.csv.export_users(test_dir + "/exported_user.csv")
  #   assert sum(
  #     1 for line in open(test_dir + "/exported_user.csv")
  #   ) == 7, "exported file should have the same line number as imported file"
  #   assert filecmp.cmp(
  #     "resources/test/user2.csv",
  #     test_dir + "/exported_user.csv",
  #     shallow=True
  #   ), "exported file should be the same as imported file"
