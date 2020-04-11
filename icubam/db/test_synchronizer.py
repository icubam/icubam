import os
import time
import tempfile
from absl.testing import absltest
from icubam.db import store, synchronizer
import sqlalchemy as sqla

class SynchronizerTest(absltest.TestCase):
  def setUp(self):
    store_factory = store.StoreFactory(
      sqla.create_engine("sqlite:///:memory:", echo=True)
    )
    self.db = store_factory.create()
    self.csv = synchronizer.CSVSynchcronizer(self.db)

  def gen_bed_counts(self, icu_name, region_name, amount):
    bed_counts = {}
    values = range(amount)
    start_time = time.now()
    for index, value in enumerate(values):
      bc = {'icu_name': icu_name,
        'n_covid_occ': value,
        'n_covid_free': value,
        'n_ncovid_occ': value,
        'n_ncovid_free': value,
        'n_covid_deaths': value,
        'n_covid_healed': value,
        'n_covid_refused': value,
        'n_covid_transfered', value,
        'timestamp'
            }
      self.store.update_bed_count_for_icu(
        self.admin_user_id,
        BedCount(
          icu_id=icu_id,
          n_covid_occ=value,
          create_date=add_seconds(now, index)
        )
      )
    return icu_id
  def test_sync_bed_counts(self):
    region_id1 = self.add_region(region_name)
    icu_id = self.add_icu(icu_name, region_id=region_id, is_active=is_active)



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

    self.assertLen(
      self.db.get_user_by_phone("333").icus, 2,
      "This user should be registered for 2 ICUs."
    )

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
    icus = self.db.get_icus()
    str_buf = self.csv.export_icus()
    # Add a row for the header:
    self.assertLen(
      str_buf.splitlines(),
      len(icus) + 1, "Number of rows should be the same."
    )