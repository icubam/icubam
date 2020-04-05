from collections import defaultdict
import os
import time

from absl.testing import absltest
from datetime import datetime, timedelta
import icubam.db.store as db_store
from icubam.db.store import Store, BedCount, ExternalClient, ICU, Region, User
from icubam import config
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


def add_seconds(dt, seconds):
  return dt + timedelta(seconds=seconds)


def key_by_name_and_create_date(bed_counts):
  values = {}
  for bed_count in bed_counts:
    values[(bed_count.icu.name, bed_count.create_date)] = bed_count.n_covid_occ
  return values


class StoreTest(absltest.TestCase):

  def setUp(self):
    store = Store(create_engine("sqlite:///:memory:", echo=True))
    self.admin_user_id = store.add_user(
        User(
            name="admin",
            telephone="1",
            email="admin@test.org",
            is_active=True,
            is_admin=True))
    self.manager_user_id = store.add_user(
        User(
            name="manager",
            telephone="2",
            email="manager@test.org",
            is_active=True))
    self.store = store
    self.session = None

  # Helper functions.
  def add_region(self, name="region"):
    return self.store.add_region(
        self.admin_user_id, Region(name=name), session=self.session)

  def add_icu(self, name="icu", region_id=None):
    return self.store.add_icu(
        self.admin_user_id,
        ICU(name=name, region_id=region_id),
        session=self.session)

  def test_add_region(self):
    store = self.store
    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    region = store.get_region(region_id1, session=self.session)
    self.assertEqual(region.name, "region1")
    self.assertIsNotNone(region.create_date)
    self.assertEqual(region.last_modified, region.create_date)

    region = store.get_region(region_id2, session=self.session)
    self.assertEqual(region.name, "region2")

  def test_get_regions(self):
    self.add_region("region1")
    self.add_region("region2")
    regions = self.store.get_regions(session=self.session)
    self.assertItemsEqual([region.name for region in regions],
                          ["region1", "region2"])

  def test_update_region(self):
    store = self.store
    region_id = self.add_region("foo")
    # Update the name of the region.
    store.update_region(
        self.admin_user_id, region_id, {"name": "bar"}, session=self.session)

    region = store.get_region(region_id, session=self.session)
    self.assertEqual(region.name, "bar")

  def test_update_missing_region(self):
    store = self.store
    store.update_region(
        self.admin_user_id, 1, {"name": "foo"}, session=self.session)
    self.assertIsNone(store.get_region(1, session=self.session))

  def test_add_icu(self):
    store = self.store
    icu = ICU(
        name="test",
        dept="dept",
        city="city",
        country="country",
        lat=1.23,
        long=4.56,
        telephone="123456")
    icu_id = store.add_icu(self.admin_user_id, icu, session=self.session)
    self.assertEqual(icu_id, 1)

    icu = store.get_icu(icu_id, session=self.session)
    self.assertEqual(icu.name, "test")
    self.assertEqual(icu.dept, "dept")
    self.assertEqual(icu.city, "city")
    self.assertEqual(icu.country, "country")
    self.assertEqual(icu.lat, 1.23)
    self.assertEqual(icu.long, 4.56)
    self.assertEqual(icu.telephone, "123456")

  def test_get_missing_icu(self):
    self.assertIsNone(self.store.get_icu(1, session=self.session))

  def test_assign_user_as_icu_manager(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    user_id = self.manager_user_id
    icu_id = self.add_icu()
    # User doesn't manager the ICU yet.
    self.assertFalse(store.manages_icu(user_id, icu_id, session=session))

    store.assign_user_as_icu_manager(
        admin_user_id, user_id, icu_id, session=session)
    self.assertTrue(store.manages_icu(user_id, icu_id, session=session))
    # Assigning again should fail.
    with self.assertRaises(IntegrityError):
      store.assign_user_as_icu_manager(
          admin_user_id, user_id, icu_id, session=session)

    # Now remove the user.
    store.remove_manager_user_from_icu(
        admin_user_id, user_id, icu_id, session=session)
    self.assertFalse(store.manages_icu(user_id, icu_id, session=session))

  def test_get_managed_icus(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    user_id = self.manager_user_id

    icu_id1 = self.add_icu("icu1")
    store.assign_user_as_icu_manager(
        admin_user_id, user_id, icu_id1, session=session)

    icus = store.get_managed_icus(user_id, session=session)
    self.assertItemsEqual([icu.name for icu in icus], ["icu1"])

    icu_id2 = self.add_icu("icu2")
    store.assign_user_as_icu_manager(
        admin_user_id, user_id, icu_id2, session=session)

    icus = store.get_managed_icus(user_id, session=session)
    self.assertItemsEqual([icu.name for icu in icus], ["icu1", "icu2"])

    # Admins should be able to manage all ICUs.
    icus = store.get_managed_icus(admin_user_id, session=session)
    self.assertItemsEqual([icu.name for icu in icus], ["icu1", "icu2"])

  def test_enable_icu_admin(self):
    store = self.store
    session = self.session
    icu_id = self.add_icu()

    store.enable_icu(self.admin_user_id, icu_id, session=session)
    self.assertTrue(store.get_icu(icu_id, session=session).is_active)

    store.disable_icu(self.admin_user_id, icu_id, session=session)
    self.assertFalse(store.get_icu(icu_id, session=session).is_active)

  def test_enable_icu(self):
    store = self.store
    session = self.session
    user_id = self.manager_user_id
    icu_id = self.add_icu()
    store.assign_user_as_icu_manager(
        self.admin_user_id, user_id, icu_id, session=session)

    store.enable_icu(user_id, icu_id, session=session)
    self.assertTrue(store.get_icu(icu_id, session=session).is_active)

    store.disable_icu(user_id, icu_id, session=session)
    self.assertFalse(store.get_icu(icu_id, session=session).is_active)

  def test_get_admins(self):
    store = self.store
    session = self.session
    store.add_user(User(name="user1"), session=session)
    store.add_user(User(name="user2"), session=session)
    self.assertEqual(len(store.get_admins(session=session)), 1)

  def test_get_users(self):
    store = self.store
    session = self.session
    store.add_user(User(name="user1"), session=session)
    store.add_user(User(name="user2"), session=session)
    users = store.get_users(session=session)
    # admin and manager already exist. See setUp.
    self.assertItemsEqual([user.name for user in users],
                          ["user1", "user2", "admin", "manager"])

  def do_test_add_user_to_icu(self, icu_id, manager_user_id):
    store = self.store
    session = self.session
    user = User(
        name="user",
        telephone="123456",
        email="user@test.org",
        description="test")
    user_id = store.add_user_to_icu(
        manager_user_id, icu_id, user, session=session)

    user = store.get_user(user_id, session=session)
    self.assertEqual(user.name, "user")
    self.assertEqual(user.telephone, "123456")
    self.assertEqual(user.email, "user@test.org")
    self.assertEqual(user.description, "test")
    self.assertEqual(user.icus[0].name, "icu")

  def test_to_dict(self):
    store = self.store
    session = self.session
    icu_id = self.add_icu()
    user = User(
        name="user",
        telephone="123456",
        email="user@test.org",
        description="test")
    user_id = store.add_user_to_icu(
        self.admin_user_id, icu_id, user, session=session)
    user = store.get_user(user_id, session=session)
    user_dict = user.to_dict()
    self.assertEqual(user_dict["name"], "user")
    self.assertEqual(user_dict["telephone"], "123456")
    self.assertEqual(user_dict["email"], "user@test.org")
    self.assertEqual(user_dict["description"], "test")
    self.assertEqual(user_dict["icus"][0]["name"], "icu")

  def test_add_user_to_icu_admin(self):
    icu_id = self.add_icu()
    self.do_test_add_user_to_icu(icu_id, self.admin_user_id)

  def test_add_user_to_icu(self):
    icu_id = self.add_icu()
    manager_user_id = self.manager_user_id
    self.store.assign_user_as_icu_manager(
        self.admin_user_id, manager_user_id, icu_id, session=self.session)
    self.do_test_add_user_to_icu(icu_id, manager_user_id)

  def test_add_user_to_icu_not_manager(self):
    icu_id = self.add_icu()
    with self.assertRaises(ValueError):
      self.do_test_add_user_to_icu(icu_id, self.manager_user_id)

  def do_test_update_user(self, icu_id, manager_user_id):
    store = self.store
    session = self.session
    user = User(name="foo")
    user_id = store.add_user_to_icu(
        manager_user_id, icu_id, user, session=session)
    store.update_user(
        manager_user_id, user_id, {"name": "bar"}, session=session)

    user = store.get_user(user_id, session=session)
    self.assertEqual(user.name, "bar")

  def test_update_user_admin(self):
    icu_id = self.add_icu()
    self.do_test_update_user(icu_id, self.admin_user_id)

  def test_update_user(self):
    icu_id = self.add_icu()
    user_id = self.manager_user_id
    self.store.assign_user_as_icu_manager(
        self.admin_user_id, user_id, icu_id, session=self.session)
    self.do_test_update_user(icu_id, user_id)

  def test_update_user_not_manager(self):
    icu_id = self.add_icu()
    with self.assertRaises(ValueError):
      self.do_test_update_user(icu_id, self.manager_user_id)

  def test_assign_user_to_icu(self):
    store = self.store
    session = self.session
    manager_user_id = self.manager_user_id
    user_id = store.add_user(User(name="user"), session=session)

    icu_id = self.add_icu()
    self.assertFalse(store.can_edit_bed_count(user_id, icu_id, session=session))

    # Manager is not managing the ICU and request should fail.
    with self.assertRaises(ValueError):
      store.assign_user_to_icu(
          manager_user_id, user_id, icu_id, session=session)

    store.assign_user_as_icu_manager(
        self.admin_user_id, manager_user_id, icu_id, session=session)
    store.assign_user_to_icu(manager_user_id, user_id, icu_id, session=session)
    self.assertTrue(store.can_edit_bed_count(user_id, icu_id, session=session))

  def test_assign_user_to_icu_admin(self):
    store = self.store
    session = self.session
    user_id = self.manager_user_id
    icu_id = self.add_icu()
    store.assign_user_to_icu(
        self.admin_user_id, user_id, icu_id, session=session)
    self.assertTrue(store.can_edit_bed_count(user_id, icu_id, session=session))

  def test_remove_user_from_icu(self):
    store = self.store
    session = self.session
    icu_id = self.add_icu()
    # Add a new user to the ICU.
    manager_user_id = self.manager_user_id
    store.assign_user_as_icu_manager(
        self.admin_user_id, manager_user_id, icu_id, session=session)
    user_id = store.add_user_to_icu(
        manager_user_id, icu_id, User(name="user"), session=session)
    self.assertTrue(store.can_edit_bed_count(user_id, icu_id, session=session))
    # Now remove the assignment.
    store.remove_user_from_icu(
        manager_user_id, user_id, icu_id, session=session)
    # User should lose access.
    self.assertFalse(store.can_edit_bed_count(user_id, icu_id, session=session))
    # Removing a non-existent assignment is a no-op.
    store.remove_user_from_icu(
        manager_user_id, user_id, icu_id, session=session)

  def test_get_managed_users(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    manager_user_id = self.manager_user_id
    icu_id1 = self.add_icu("icu1")
    store.assign_user_as_icu_manager(
        admin_user_id, manager_user_id, icu_id1, session=session)

    user1 = store.add_user_to_icu(
        manager_user_id, icu_id1, User(name="user1"), session=session)
    user2 = store.add_user_to_icu(
        manager_user_id, icu_id1, User(name="user2"), session=session)

    icu_id2 = self.add_icu("icu2")
    store.assign_user_as_icu_manager(
        admin_user_id, manager_user_id, icu_id2, session=session)

    user3 = store.add_user_to_icu(
        manager_user_id, icu_id2, User(name="user3"), session=session)

    # Add a user to a ICU which is not managed by the manager user. This should
    # not be present in the set of managed users.
    icu_id3 = self.add_icu("icu3")
    user4 = store.add_user_to_icu(
        admin_user_id, icu_id3, User(name="user4"), session=session)

    users = store.get_managed_users(manager_user_id, session=session)
    self.assertItemsEqual([user.name for user in users],
                          ["user1", "user2", "user3"])

  def test_auth_user(self):
    store = self.store
    session = self.session
    user_id = self.manager_user_id
    store.update_user(
        self.admin_user_id,
        user_id, {"password_hash": store.get_password_hash("secret")},
        session=session)
    self.assertEqual(
        store.auth_user("manager@test.org", "secret", session=session), user_id)
    self.assertIsNone(
        store.auth_user("manager@test.org", "other_secret", session=session))
    self.assertIsNone(
        store.auth_user("admin@test.org", "secret", session=session))

  def test_can_edit_bed_count_admin(self):
    icu_id = self.add_icu()
    self.assertTrue(
        self.store.can_edit_bed_count(
            self.admin_user_id, icu_id, session=self.session))

  def test_can_edit_bed_count(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id

    icu_id1 = self.add_icu("icu1")
    user_id1 = store.add_user_to_icu(
        admin_user_id, icu_id1, User(name="user1"), session=session)

    icu_id2 = self.add_icu("icu2")
    user_id2 = store.add_user_to_icu(
        admin_user_id, icu_id2, User(name="user2"), session=session)
    user_id3 = store.add_user_to_icu(
        admin_user_id, icu_id2, User(name="user3"), session=session)

    # Users can only edit ICUs that they are assigned.
    self.assertTrue(
        store.can_edit_bed_count(user_id1, icu_id1, session=session))
    self.assertFalse(
        store.can_edit_bed_count(user_id1, icu_id2, session=session))
    self.assertFalse(
        store.can_edit_bed_count(user_id2, icu_id1, session=session))
    self.assertTrue(
        store.can_edit_bed_count(user_id2, icu_id2, session=session))
    # user3 is same as user2.
    self.assertFalse(
        store.can_edit_bed_count(user_id3, icu_id1, session=session))
    self.assertTrue(
        store.can_edit_bed_count(user_id3, icu_id2, session=session))

  def test_get_bed_count_for_icu(self):
    store = self.store
    session = self.session
    icu_id = self.add_icu()
    user_id = store.add_user_to_icu(
        self.admin_user_id, icu_id, User(name="user"), session=session)
    bed_count = store.get_bed_count_for_icu(icu_id, session=session)
    self.assertIsNone(bed_count)

    bed_count = BedCount(
        icu_id=icu_id,
        n_covid_occ=1,
        n_covid_free=2,
        n_ncovid_occ=8,
        n_ncovid_free=3,
        n_covid_deaths=4,
        n_covid_healed=5,
        n_covid_refused=6,
        n_covid_transfered=7)
    store.update_bed_count_for_icu(user_id, bed_count, session=session)

    bed_count = store.get_bed_count_for_icu(icu_id, session=session)
    self.assertEqual(bed_count.n_covid_occ, 1)
    self.assertEqual(bed_count.n_covid_free, 2)
    self.assertEqual(bed_count.n_ncovid_occ, 8)
    self.assertEqual(bed_count.n_ncovid_free, 3)
    self.assertEqual(bed_count.n_covid_deaths, 4)
    self.assertEqual(bed_count.n_covid_healed, 5)
    self.assertEqual(bed_count.n_covid_refused, 6)
    self.assertEqual(bed_count.n_covid_transfered, 7)
    # ICU relationships.
    self.assertEqual(bed_count.icu.name, "icu")

    # Timestamps have second accuracy.
    time.sleep(1.1)

    next_bed_count = BedCount(
        icu_id=icu_id,
        n_covid_occ=7,
        n_covid_free=6,
        n_ncovid_occ=8,
        n_ncovid_free=5,
        n_covid_deaths=4,
        n_covid_healed=3,
        n_covid_refused=2,
        n_covid_transfered=1)
    store.update_bed_count_for_icu(user_id, next_bed_count, session=session)

    bed_count = store.get_bed_count_for_icu(icu_id, session=session)
    self.assertEqual(bed_count.n_covid_occ, 7)
    self.assertEqual(bed_count.n_covid_free, 6)
    self.assertEqual(bed_count.n_ncovid_occ, 8)
    self.assertEqual(bed_count.n_ncovid_free, 5)
    self.assertEqual(bed_count.n_covid_deaths, 4)
    self.assertEqual(bed_count.n_covid_healed, 3)
    self.assertEqual(bed_count.n_covid_refused, 2)
    self.assertEqual(bed_count.n_covid_transfered, 1)

  def add_icu_with_values(self, region_id, name, now, values):
    icu_id = self.add_icu(name, region_id=region_id)
    for index, value in enumerate(values):
      self.store.update_bed_count_for_icu(
          self.admin_user_id,
          BedCount(
              icu_id=icu_id,
              n_covid_occ=value,
              create_date=add_seconds(now, index)),
          session=self.session)
    return icu_id

  def test_get_visible_bed_counts_for_user(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    now = datetime.now()

    def get_values(user_id, max_date=None, force=False):
      return key_by_name_and_create_date(
          store.get_visible_bed_counts_for_user(
              user_id, max_date=max_date, force=force, session=session))

    icu_id1 = self.add_icu_with_values(region_id1, "icu1", now, [1, 2])
    icu_id2 = self.add_icu_with_values(region_id1, "icu2", now, [4, 3])
    icu_id3 = self.add_icu_with_values(region_id2, "icu3", now, [5])

    # Admin user should see bed counts of all ICUs.
    now_plus_1 = add_seconds(now, 1)
    self.assertDictEqual(
        get_values(admin_user_id), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5
        })

    # Restrict to now + 1.
    self.assertDictEqual(
        get_values(admin_user_id, now_plus_1), {
            ("icu1", now): 1,
            ("icu2", now): 4,
            ("icu3", now): 5
        })

    # user1 can view ICU1 and 2 as they are in the same region and user1 is
    # assigned to ICU1.
    user_id1 = store.add_user_to_icu(
        admin_user_id, icu_id1, User(name="user1"), session=session)
    self.assertDictEqual(
        get_values(user_id1), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3
        })

    # user2 can only view ICU3.
    user_id2 = store.add_user_to_icu(
        admin_user_id, icu_id3, User(name="user2"), session=session)
    self.assertDictEqual(get_values(user_id2), {("icu3", now): 5})

    # Unless we force to see everything.
    self.assertDictEqual(
        get_values(user_id2, force=True), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5,
        })

  def test_get_visible_bed_counts_in_same_region(self):
    store = self.store
    session = self.session
    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    now = datetime.now()

    icu_id1 = self.add_icu_with_values(region_id1, "icu1", now, [1, 2])
    icu_id2 = self.add_icu_with_values(region_id1, "icu2", now, [4, 3])
    icu_id3 = self.add_icu_with_values(region_id2, "icu3", now, [5])

    def get_values(icu_ids, max_date=None):
      if icu_ids:
        bed_counts = store.get_visible_bed_counts_in_same_region(
            icu_ids, max_date=max_date, session=session)
      else:
        bed_counts = store.get_latest_bed_counts(
            max_date=max_date, session=session)
      return key_by_name_and_create_date(bed_counts)

    # icu1 should return both icu1 and icu2 in region1.
    now_plus_1 = add_seconds(now, 1)
    self.assertDictEqual(
        get_values([icu_id1]), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3
        })

    # Only icu3 is in region2.
    self.assertDictEqual(get_values([icu_id3]), {("icu3", now): 5})

    # This should return all ICUs.
    self.assertDictEqual(
        get_values([icu_id1, icu_id3]), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5
        })

    now_plus_1 = add_seconds(now, 1)

    # Restrict to now + 1.
    self.assertDictEqual(
        get_values([icu_id1, icu_id3], now_plus_1), {
            ("icu1", now): 1,
            ("icu2", now): 4,
            ("icu3", now): 5
        })

  def test_add_external_client(self):
    store = self.store
    session = self.session
    external_client_id, access_key = store.add_external_client(
        self.admin_user_id,
        ExternalClient(name="client", email="client@test.org"),
        session=session)

    self.assertEqual(external_client_id, 1)
    self.assertTrue(access_key.key)
    self.assertEqual(access_key.key_hash,
                     store.get_access_key_hash(access_key.key))

    external_client = store.get_external_client(
        external_client_id, session=session)
    self.assertEqual(external_client.name, "client")
    self.assertEqual(external_client.email, "client@test.org")
    self.assertEqual(external_client.access_key_hash, access_key.key_hash)
    self.assertIsNotNone(external_client.create_date)
    self.assertEqual(external_client.last_modified, external_client.create_date)
    self.assertTrue(external_client.access_key_valid)

  def test_update_external_client(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    external_client_id, _ = store.add_external_client(
        admin_user_id, ExternalClient(name="foo"), session=session)

    now = datetime.now()
    expiration_date = add_seconds(now, 60)

    store.update_external_client(
        admin_user_id,
        external_client_id, {
            "name": "bar",
            "email": "bar@test.org",
            "expiration_date": expiration_date
        },
        session=session)

    external_client = store.get_external_client(
        external_client_id, session=session)
    self.assertEqual(external_client.name, "bar")
    self.assertEqual(external_client.email, "bar@test.org")
    self.assertEqual(external_client.expiration_date, expiration_date)
    self.assertTrue(external_client.access_key_valid)

    store.update_external_client(
        admin_user_id,
        external_client_id, {"expiration_date": now},
        session=session)
    external_client = store.get_external_client(
        external_client_id, session=session)
    self.assertFalse(external_client.access_key_valid)

  def test_get_external_clients(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    store.add_external_client(
        admin_user_id, ExternalClient(name="client1"), session=session)
    store.add_external_client(
        admin_user_id, ExternalClient(name="client2"), session=session)
    external_clients = store.get_external_clients(session=session)
    self.assertItemsEqual(
        [external_client.name for external_client in external_clients],
        ["client1", "client2"])
    self.assertNotEqual(external_clients[0].access_key_hash,
                        external_clients[1].access_key_hash)

  def test_reset_external_client_access_key(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    external_client_id, access_key = store.add_external_client(
        admin_user_id,
        ExternalClient(
            name="client", expiration_date=add_seconds(datetime.now(), 60)),
        session=session)

    new_access_key = store.reset_external_client_access_key(
        admin_user_id, external_client_id, session=session)

    self.assertTrue(new_access_key.key)
    self.assertNotEqual(new_access_key.key, access_key.key)
    self.assertEqual(new_access_key.key_hash,
                     store.get_access_key_hash(new_access_key.key))

    external_client = store.get_external_client(
        external_client_id, session=session)
    self.assertEqual(external_client.access_key_hash, new_access_key.key_hash)
    self.assertIsNone(external_client.expiration_date)
    self.assertTrue(external_client.access_key_valid)

  def test_auth_external_client(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    external_client_id1, access_key1 = store.add_external_client(
        admin_user_id, ExternalClient(name="client1"), session=session)
    external_client_id2, access_key2 = store.add_external_client(
        admin_user_id, ExternalClient(name="client2"), session=session)

    external_client_id = store.auth_external_client(
        access_key1.key, session=session)
    self.assertEqual(external_client_id, external_client_id1)

    external_client_id = store.auth_external_client(
        access_key2.key, session=session)
    self.assertEqual(external_client_id, external_client_id2)

    self.assertIsNone(store.auth_external_client("test", session=session))

  def test_assign_external_client_to_region(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    external_client_id, _ = store.add_external_client(
        admin_user_id, ExternalClient(name="client"), session=session)

    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    def get_region_ids():
      external_client = store.get_external_client(
          external_client_id, session=session)
      return [region.region_id for region in external_client.regions]

    store.assign_external_client_to_region(
        admin_user_id, external_client_id, region_id1, session=session)
    self.assertItemsEqual(get_region_ids(), [region_id1])

    # Assigning again should fail.
    with self.assertRaises(IntegrityError):
      store.assign_external_client_to_region(
          admin_user_id, external_client_id, region_id1, session=session)

    # Assign to another region.
    store.assign_external_client_to_region(
        admin_user_id, external_client_id, region_id2, session=session)
    self.assertItemsEqual(get_region_ids(), [region_id1, region_id2])

    store.remove_external_client_from_region(
        admin_user_id, external_client_id, region_id1, session=session)
    self.assertItemsEqual(get_region_ids(), [region_id2])

    # Removing again is a no-op.
    store.remove_external_client_from_region(
        admin_user_id, external_client_id, region_id1, session=session)

  def test_get_bed_counts_for_external_client(self):
    store = self.store
    session = self.session
    admin_user_id = self.admin_user_id
    external_client_id, _ = store.add_external_client(
        admin_user_id, ExternalClient(name="client"), session=session)

    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    now = datetime.now()

    icu_id1 = self.add_icu_with_values(region_id1, "icu1", now, [1, 2])
    icu_id2 = self.add_icu_with_values(region_id1, "icu2", now, [4, 3])
    icu_id3 = self.add_icu_with_values(region_id2, "icu3", now, [5])

    def get_values(latest=True, max_date=None):
      return key_by_name_and_create_date(
          store.get_bed_counts_for_external_client(
              external_client_id,
              latest=latest,
              max_date=max_date,
              session=session))

    # Client is not assigned to any region.
    self.assertFalse(get_values())

    store.assign_external_client_to_region(
        admin_user_id, external_client_id, region_id1, session=session)
    now_plus_1 = add_seconds(now, 1)
    self.assertDictEqual(
        get_values(latest=True), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3
        })

    self.assertDictEqual(
        get_values(latest=False), {
            ("icu1", now): 1,
            ("icu1", now_plus_1): 2,
            ("icu2", now): 4,
            ("icu2", now_plus_1): 3
        })

    self.assertDictEqual(
        get_values(max_date=now_plus_1), {
            ("icu1", now): 1,
            ("icu2", now): 4,
        })

    self.assertDictEqual(
        get_values(latest=False, max_date=now_plus_1), {
            ("icu1", now): 1,
            ("icu2", now): 4,
        })

    store.assign_external_client_to_region(
        admin_user_id, external_client_id, region_id2, session=session)
    self.assertDictEqual(
        get_values(latest=True), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5
        })

    self.assertDictEqual(
        get_values(latest=False), {
            ("icu1", now): 1,
            ("icu1", now_plus_1): 2,
            ("icu2", now): 4,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5
        })

  def test_get_bed_counts(self):
    region_id = self.add_region("region")

    now = datetime.now()

    icu_id1 = self.add_icu_with_values(region_id, "icu1", now, [1, 2])
    icu_id2 = self.add_icu_with_values(region_id, "icu2", now, [4, 3])
    icu_id3 = self.add_icu_with_values(region_id, "icu3", now, [5])

    def get_values(icu_ids=None, latest=True, max_date=None):
      return key_by_name_and_create_date(
          self.store.get_bed_counts(
              icu_ids=icu_ids,
              latest=latest,
              max_date=max_date,
              session=self.session))

    now_plus_1 = add_seconds(now, 1)
    self.assertDictEqual(
        get_values(latest=True), {
            ("icu1", now_plus_1): 2,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5
        })

    self.assertDictEqual(
        get_values(latest=False), {
            ("icu1", now): 1,
            ("icu1", now_plus_1): 2,
            ("icu2", now): 4,
            ("icu2", now_plus_1): 3,
            ("icu3", now): 5
        })

    self.assertDictEqual(
        get_values(max_date=now_plus_1), {
            ("icu1", now): 1,
            ("icu2", now): 4,
            ("icu3", now): 5
        })

    self.assertDictEqual(
        get_values(icu_ids=[icu_id1, icu_id3], latest=True), {
            ("icu1", now_plus_1): 2,
            ("icu3", now): 5
        })

    self.assertDictEqual(
        get_values(icu_ids=[icu_id1, icu_id3], latest=False), {
            ("icu1", now): 1,
            ("icu1", now_plus_1): 2,
            ("icu3", now): 5
        })

    self.assertDictEqual(
        get_values(icu_ids=[icu_id1, icu_id3], max_date=now_plus_1), {
            ("icu1", now): 1,
            ("icu3", now): 5
        })

  def test_create_store_for_sqlite_db(self):
    cfg = config.Config(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../resources/test.toml"))
    store = db_store.create_store_for_sqlite_db(cfg)

  def test_session(self):
    store = self.store
    session = self.session
    user_id1 = store.add_user(User(name="user1"), session=session)
    user1 = store.get_user(user_id1, session=session)

    user_id2 = store.add_user(User(name="user2"), session=session)
    user2 = store.get_user(user_id2, session=session)

    # Objects should not be detached.
    user1.icus
    user2.icus


class StoreWithSessionTest(StoreTest):

  def setUp(self):
    super().setUp()
    self.session = self.store._session()
