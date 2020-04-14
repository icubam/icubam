from datetime import datetime, timedelta

import pandas as pd
import sqlalchemy as sqla
from absl.testing import absltest
from dateutil import tz

from icubam.db import store, synchronizer


class StoreSynchronizerTest(absltest.TestCase):
  def setUp(self):
    store_factory = store.StoreFactory(
      sqla.create_engine("sqlite:///:memory:", echo=True)
    )
    self.db = store_factory.create()
    self.sync = synchronizer.StoreSynchronizer(self.db)
    self.sync.prepare()

    # Helper functions.
  def add_region(self, name="region"):
    return self.db.add_region(
      self.sync._default_admin, store.Region(name=name)
    )

  def add_icu(self, name="icu", region_id=None, is_active=True):
    return self.db.add_icu(
      self.sync._default_admin,
      store.ICU(name=name, region_id=region_id, is_active=is_active)
    )

  def gen_bed_count_set(self, start_time, icu_name, amount):
    bed_counts = []
    values = range(amount)
    for value in values:
      bc = {
        'icu_name': icu_name,
        'n_covid_occ': value,
        'n_covid_free': value,
        'n_ncovid_occ': value,
        'n_ncovid_free': value,
        'n_covid_deaths': value,
        'n_covid_healed': value,
        'n_covid_refused': value,
        'n_covid_transfered': value,
        'create_date': start_time + timedelta(hours=value)
      }
      bed_counts.append(bc)
    return bed_counts

  def gen_bed_counts(
    self, start_time, region_names, icu_base_names, num_icus, do_adds=True
  ):
    bed_counts = []
    for region_name in region_names:
      if do_adds:
        region_id = self.add_region(region_name)
      for icu_base_name in icu_base_names:
        icu_name = f'{region_name}_{icu_base_name}'
        if do_adds:
          self.add_icu(icu_name, region_id=region_id, is_active=True)
        bed_counts.extend(
          self.gen_bed_count_set(start_time, icu_name, num_icus)
        )
    return bed_counts

  def test_sync_bed_counts(self):
    region_names = ['Region1', 'Region2']
    icu_base_names = ['ICU1', 'ICU2', 'ICU3']
    num_icus = 10
    bed_counts = []
    start_time = datetime.now(tz.tzutc())

    # Inject a first set of bed_countss
    bed_counts_dict = self.gen_bed_counts(
      start_time, region_names, icu_base_names, num_icus
    )
    bed_counts_df = pd.DataFrame(bed_counts_dict)
    self.sync.sync_bed_counts(bed_counts_df)

    # Make sure the right amount are there
    bed_counts = self.db.get_bed_counts()
    self.assertLen(
      bed_counts,
      len(region_names) * len(icu_base_names) * num_icus
    )

    # Make sure latests returns just the subset and their times are correct
    bed_counts = self.db.get_latest_bed_counts()
    self.assertLen(bed_counts, len(region_names) * len(icu_base_names))
    self.assertEqual(
      bed_counts[0].create_date.replace(tzinfo=tz.tzutc()),
      bed_counts_df['create_date'].max().to_pydatetime()
    )

    # Make sure if we re-inject we get twice as much back
    self.sync.sync_bed_counts(bed_counts_df)
    bed_counts = self.db.get_bed_counts()
    self.assertLen(
      bed_counts,
      len(region_names) * len(icu_base_names) * num_icus * 2
    )

    # Now if we re-inject with more future times, make sure they
    # override the elements in 'latest'
    bed_counts_dict = self.gen_bed_counts(
      start_time + timedelta(days=2),
      region_names,
      icu_base_names,
      num_icus,
      do_adds=False
    )
    bed_counts_df = pd.DataFrame(bed_counts_dict)
    self.sync.sync_bed_counts(bed_counts_df)
    bed_counts = self.db.get_latest_bed_counts()
    self.assertEqual(
      bed_counts[0].create_date.replace(tzinfo=tz.tzutc()),
      bed_counts_df['create_date'].max().to_pydatetime()
    )

    # Test that field can be set to None
    bed_counts_dict = self.gen_bed_counts(
      start_time + timedelta(days=11),
      region_names,
      icu_base_names,
      num_icus,
      do_adds=False
    )
    bed_counts_df = pd.DataFrame(bed_counts_dict)
    bed_counts_df['n_covid_healed'] = None
    self.sync.sync_bed_counts(bed_counts_df)
    bed_counts = self.db.get_latest_bed_counts()
    self.assertIsNone(bed_counts[0].n_covid_healed)



  def test_sync_bed_counts_exceptions(self):
    # Without existent ICU
    start_time = datetime.now(tz.tzutc())
    bed_counts_df = pd.DataFrame(
      self.gen_bed_count_set(start_time, 'Test', 10)
    )
    with self.assertRaises(KeyError):
      self.sync.sync_bed_counts(bed_counts_df)

    # Without UTC Time
    region_id = self.add_region('Region')
    self.add_icu('ICU', region_id=region_id, is_active=True)
    start_time = datetime.now()
    bed_counts_df = pd.DataFrame(self.gen_bed_count_set(start_time, 'ICU', 10))
    with self.assertRaises(ValueError):
      self.sync.sync_bed_counts(bed_counts_df)


class CSVTest(absltest.TestCase):
  def setUp(self):
    store_factory = store.StoreFactory(
      sqla.create_engine("sqlite:///:memory:", echo=True)
    )
    self.db = store_factory.create()
    self.csv = synchronizer.CSVSynchronizer(self.db)

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
    self.db.get_user_by_phone("111").description

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

    icus = self.db.get_icus()
    str_buf = self.csv.export_icus()
    # Add a row for the header:
    self.assertLen(
      str_buf.splitlines(),
      len(icus) + 1, "Number of rows should be the same."
    )
