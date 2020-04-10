import os
import time

from absl.testing import absltest
import icubam.db.store as db_store
from icubam.db.store import Store, StoreFactory, BedCount, ExternalClient, ICU, Region, User
from icubam.db.csv import CSV
import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import DetachedInstanceError
import tempfile
import filecmp


class CSVTest(absltest.TestCase):
  def setUp(self):
    store_factory = StoreFactory(
      create_engine("sqlite:///:memory:", echo=True)
    )
    store = store_factory.create()
    self.store = store
    self.csv = CSV(store)
    self.admin_id = self.csv.get_default_admin()

  def test_import_icus(self):
    # import icu.csv, contain 3 ICUs
    self.csv.import_icus(self.admin_id, "resources/test/icu.csv", False)
    n_icu = len(self.store.get_icus())
    assert n_icu == 3, "3 ICUs should be on db, got " + str(n_icu)
    phone1 = self.store.get_icu_by_name("hopital1").telephone

    # import icu2.csv, contain 4 ICUs
    # one new and 3 updated one
    self.csv.import_icus(self.admin_id, "resources/test/icu2.csv", False)
    n_icu = len(self.store.get_icus())
    assert n_icu == 4, "4 ICUs should be on db, got " + str(n_icu)
    phone2 = self.store.get_icu_by_name("hopital1").telephone
    assert phone1 == phone2, "ICU data should not have been updated without forceUpdate"

    # import icu2.csv again but with forceUpdate enabled
    self.csv.import_icus(self.admin_id, "resources/test/icu2.csv", True)
    n_icu = len(self.store.get_icus())
    assert n_icu == 4, "4 ICUs should be on db, got " + str(n_icu)
    phone3 = self.store.get_icu_by_name("hopital1").telephone
    assert phone2 != phone3, "ICU data should have been updated with forceUpdate"

  def test_import_users(self):
    self.csv.import_icus(self.admin_id, "resources/test/icu2.csv", False)

    # import user1.csv, contain 4 lines but only 3 users (one user is registered to 2 ICUs)
    self.csv.import_users(self.admin_id, "resources/test/user.csv", False)
    n_user = len(self.store.get_users())
    assert n_user == 4, "4 users should be on db(3 imported + admin), got " + str(
      n_user
    )
    desc1 = self.store.get_user_by_phone("111").description

    # import user2.csv, contain one more user, register an existing user to a new icu, and updated description
    self.csv.import_users(self.admin_id, "resources/test/user2.csv", False)
    n_user = len(self.store.get_users())
    assert n_user == 5, "5 users should be on db(4 imported + admin), got " + str(
      n_user
    )
    desc2 = self.store.get_user_by_phone("111").description
    assert desc1 == desc2, "user desc should not have been updated without forceUpdate"
    assert len(
      self.store.get_user_by_phone("333").icus
    ) == 2, "this user should be registered for 2 ICUs"

    # import user2.csv again but with forceUpdate
    self.csv.import_users(self.admin_id, "resources/test/user2.csv", True)
    n_user = len(self.store.get_users())
    assert n_user == 5, "5 users should be on db(4 imported + admin), got " + str(
      n_user
    )
    desc3 = self.store.get_user_by_phone("111").description
    assert desc2 != desc3, "user desc should have been updated with forceUpdate"

  def test_export_icus(self):
    self.csv.import_icus(self.admin_id, "resources/test/icu2.csv", False)

    test_dir = tempfile.mkdtemp()
    self.csv.export_icus(test_dir + "/exported_icu.csv")
    assert sum(
      1 for line in open(test_dir + "/exported_icu.csv")
    ) == 5, "exported file should have the same line number as imported file"
    assert filecmp.cmp(
      "resources/test/icu2.csv", test_dir + "/exported_icu.csv", shallow=True
    ), "exported file should be the same as imported file"

  def test_export_users(self):
    self.csv.import_icus(self.admin_id, "resources/test/icu2.csv", False)
    self.csv.import_users(self.admin_id, "resources/test/user2.csv", False)

    test_dir = tempfile.mkdtemp()
    self.csv.export_users(test_dir + "/exported_user.csv")
    assert sum(
      1 for line in open(test_dir + "/exported_user.csv")
    ) == 7, "exported file should have the same line number as imported file"
    assert filecmp.cmp(
      "resources/test/user2.csv",
      test_dir + "/exported_user.csv",
      shallow=True
    ), "exported file should be the same as imported file"


if __name__ == "__main__":
  absltest.main()
