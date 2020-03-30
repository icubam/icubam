import os
import tempfile
import time

from absl.testing import absltest
from datetime import datetime, timedelta
import icubam.db.store as db_store
from icubam.db.store import Store, BedCount, ICU, Region, User
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


class SQLiteDBTest(absltest.TestCase):

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

  # Helper functions.
  def add_region(self, name="region"):
    return self.store.add_region(self.admin_user_id, Region(name=name))

  def add_icu(self, name="icu"):
    return self.store.add_icu(self.admin_user_id, ICU(name=name))

  def test_add_region(self):
    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    region = self.store.get_region(region_id1)
    self.assertEqual(region.name, "region1")
    self.assertIsNotNone(region.create_date)
    self.assertEqual(region.last_modified, region.create_date)

    region = self.store.get_region(region_id2)
    self.assertEqual(region.name, "region2")

  def test_get_regions(self):
    self.add_region("region1")
    self.add_region("region2")
    regions = self.store.get_regions()
    self.assertItemsEqual([region.name for region in regions],
                          ["region1", "region2"])

  def test_update_region(self):
    region_id = self.add_region("foo")
    # Update the name of the region.
    self.store.update_region(self.admin_user_id, region_id, {"name": "bar"})

    region = self.store.get_region(region_id)
    self.assertEqual(region.name, "bar")

  def test_update_missing_region(self):
    self.store.update_region(self.admin_user_id, 1, {"name": "foo"})
    self.assertIsNone(self.store.get_region(1))

  def test_add_icu(self):
    icu = ICU(
        name="test",
        dept="dept",
        city="city",
        country="country",
        lat=1.23,
        long=4.56,
        telephone="123456")
    icu_id = self.store.add_icu(self.admin_user_id, icu)
    self.assertEqual(icu_id, 1)

    icu = self.store.get_icu(icu_id)
    self.assertEqual(icu.name, "test")
    self.assertEqual(icu.dept, "dept")
    self.assertEqual(icu.city, "city")
    self.assertEqual(icu.country, "country")
    self.assertEqual(icu.lat, 1.23)
    self.assertEqual(icu.long, 4.56)
    self.assertEqual(icu.telephone, "123456")

  def test_get_missing_icu(self):
    self.assertIsNone(self.store.get_icu(1))

  def test_assign_user_as_icu_manager(self):
    store = self.store
    admin_user_id = self.admin_user_id
    user_id = self.manager_user_id
    icu_id = self.add_icu()
    # User doesn't manager the ICU yet.
    self.assertFalse(store.manages_icu(user_id, icu_id))

    store.assign_user_as_icu_manager(admin_user_id, user_id, icu_id)
    self.assertTrue(store.manages_icu(user_id, icu_id))
    # Assigning again should fail.
    with self.assertRaises(IntegrityError):
      store.assign_user_as_icu_manager(admin_user_id, user_id, icu_id)

  def test_get_managed_icus(self):
    store = self.store
    admin_user_id = self.admin_user_id
    user_id = self.manager_user_id

    icu_id1 = self.add_icu("icu1")
    store.assign_user_as_icu_manager(admin_user_id, user_id, icu_id1)

    icu_id2 = self.add_icu("icu2")
    store.assign_user_as_icu_manager(admin_user_id, user_id, icu_id2)

    icus = store.get_managed_icus(user_id)
    self.assertItemsEqual([icu.name for icu in icus], ["icu1", "icu2"])

  def test_enable_icu_admin(self):
    store = self.store
    icu_id = self.add_icu()

    store.enable_icu(self.admin_user_id, icu_id)
    self.assertTrue(store.get_icu(icu_id).is_active)

    store.disable_icu(self.admin_user_id, icu_id)
    self.assertFalse(store.get_icu(icu_id).is_active)

  def test_enable_icu(self):
    store = self.store
    user_id = self.manager_user_id
    icu_id = self.add_icu()
    store.assign_user_as_icu_manager(self.admin_user_id, user_id, icu_id)

    store.enable_icu(user_id, icu_id)
    self.assertTrue(store.get_icu(icu_id).is_active)

    store.disable_icu(user_id, icu_id)
    self.assertFalse(store.get_icu(icu_id).is_active)

  def do_test_add_user_to_icu(self, icu_id, manager_user_id):
    user = User(
        name="user",
        telephone="123456",
        email="user@test.org",
        description="test")
    user_id = self.store.add_user_to_icu(manager_user_id, icu_id, user)

    user = self.store.get_user(user_id)
    self.assertEqual(user.name, "user")
    self.assertEqual(user.telephone, "123456")
    self.assertEqual(user.email, "user@test.org")
    self.assertEqual(user.description, "test")
    self.assertEqual(user.icus[0].name, "icu")

  def test_add_user_to_icu_admin(self):
    icu_id = self.add_icu()
    self.do_test_add_user_to_icu(icu_id, self.admin_user_id)

  def test_add_user_to_icu(self):
    icu_id = self.add_icu()
    manager_user_id = self.manager_user_id
    self.store.assign_user_as_icu_manager(self.admin_user_id, manager_user_id,
                                          icu_id)
    self.do_test_add_user_to_icu(icu_id, manager_user_id)

  def test_add_user_to_icu_not_manager(self):
    icu_id = self.add_icu()
    with self.assertRaises(ValueError):
      self.do_test_add_user_to_icu(icu_id, self.manager_user_id)

  def do_test_update_user(self, icu_id, manager_user_id):
    store = self.store
    user = User(name="foo")
    user_id = store.add_user_to_icu(manager_user_id, icu_id, user)
    store.update_user(manager_user_id, user_id, {"name": "bar"})

    user = store.get_user(user_id)
    self.assertEqual(user.name, "bar")

  def test_update_user_admin(self):
    icu_id = self.add_icu()
    self.do_test_update_user(icu_id, self.admin_user_id)

  def test_update_user(self):
    icu_id = self.add_icu()
    user_id = self.manager_user_id
    self.store.assign_user_as_icu_manager(self.admin_user_id, user_id, icu_id)
    self.do_test_update_user(icu_id, user_id)

  def test_update_user_not_manager(self):
    icu_id = self.add_icu()
    with self.assertRaises(ValueError):
      self.do_test_update_user(icu_id, self.manager_user_id)

  def test_assign_user_to_icu(self):
    store = self.store
    manager_user_id = self.manager_user_id
    user_id = self.store.add_user(User(name="user"))

    icu_id = self.add_icu()
    self.assertFalse(store.can_edit_bed_count(user_id, icu_id))

    # Manager is not managing the ICU and request should fail.
    with self.assertRaises(ValueError):
      store.assign_user_to_icu(manager_user_id, user_id, icu_id)

    store.assign_user_as_icu_manager(self.admin_user_id, manager_user_id,
                                     icu_id)
    store.assign_user_to_icu(manager_user_id, user_id, icu_id)
    self.assertTrue(store.can_edit_bed_count(user_id, icu_id))

  def test_assign_user_to_icu_admin(self):
    store = self.store
    user_id = self.manager_user_id
    icu_id = self.add_icu()
    store.assign_user_to_icu(self.admin_user_id, user_id, icu_id)
    self.assertTrue(store.can_edit_bed_count(user_id, icu_id))

  def test_remove_user_from_icu(self):
    store = self.store
    icu_id = self.add_icu()
    # Add a new user to the ICU.
    manager_user_id = self.manager_user_id
    store.assign_user_as_icu_manager(self.admin_user_id, manager_user_id,
                                     icu_id)
    user_id = self.store.add_user_to_icu(manager_user_id, icu_id,
                                         User(name="user"))
    self.assertTrue(store.can_edit_bed_count(user_id, icu_id))
    # Now remove the assignment.
    store.remove_user_from_icu(manager_user_id, user_id, icu_id)
    # User should lose access.
    self.assertFalse(store.can_edit_bed_count(user_id, icu_id))
    # Removing a non-existent assignment is a no-op.
    store.remove_user_from_icu(manager_user_id, user_id, icu_id)

  def test_get_managed_users(self):
    store = self.store
    admin_user_id = self.admin_user_id
    manager_user_id = self.manager_user_id
    icu_id1 = self.add_icu("icu1")
    store.assign_user_as_icu_manager(admin_user_id, manager_user_id, icu_id1)

    user1 = store.add_user_to_icu(manager_user_id, icu_id1, User(name="user1"))
    user2 = store.add_user_to_icu(manager_user_id, icu_id1, User(name="user2"))

    icu_id2 = self.add_icu("icu2")
    store.assign_user_as_icu_manager(admin_user_id, manager_user_id, icu_id2)

    user3 = store.add_user_to_icu(manager_user_id, icu_id2, User(name="user3"))

    # Add a user to a ICU which is not managed by the manager user. This should
    # not be present in the set of managed users.
    icu_id3 = self.add_icu("icu3")
    user4 = store.add_user_to_icu(admin_user_id, icu_id3, User(name="user4"))

    users = store.get_managed_users(manager_user_id)
    self.assertItemsEqual([user.name for user in users],
                          ["user1", "user2", "user3"])

  def test_auth_user(self):
    store = self.store
    user_id = self.manager_user_id
    store.update_user(self.admin_user_id, user_id,
                      {"password_hash": store.get_password_hash("secret")})
    self.assertEqual(store.auth_user("manager@test.org", "secret"), user_id)
    self.assertIsNone(store.auth_user("manager@test.org", "other_secret"))
    self.assertIsNone(store.auth_user("admin@test.org", "secret"))

  def test_can_edit_bed_count_admin(self):
    icu_id = self.add_icu()
    self.assertTrue(self.store.can_edit_bed_count(self.admin_user_id, icu_id))

  def test_can_edit_bed_count(self):
    store = self.store
    admin_user_id = self.admin_user_id

    icu_id1 = self.add_icu("icu1")
    user_id1 = store.add_user_to_icu(admin_user_id, icu_id1, User(name="user1"))

    icu_id2 = self.add_icu("icu2")
    user_id2 = store.add_user_to_icu(admin_user_id, icu_id2, User(name="user2"))
    user_id3 = store.add_user_to_icu(admin_user_id, icu_id2, User(name="user3"))

    # Users can only edit ICUs that they are assigned.
    self.assertTrue(store.can_edit_bed_count(user_id1, icu_id1))
    self.assertFalse(store.can_edit_bed_count(user_id1, icu_id2))
    self.assertFalse(store.can_edit_bed_count(user_id2, icu_id1))
    self.assertTrue(store.can_edit_bed_count(user_id2, icu_id2))
    # user3 is same as user2.
    self.assertFalse(store.can_edit_bed_count(user_id3, icu_id1))
    self.assertTrue(store.can_edit_bed_count(user_id3, icu_id2))

  def test_get_bed_count_for_icu(self):
    store = self.store
    icu_id = self.add_icu()
    user_id = store.add_user_to_icu(self.admin_user_id, icu_id,
                                    User(name="user"))
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
    store.update_bed_count_for_icu(user_id, bed_count)

    bed_count = store.get_bed_count_for_icu(icu_id)
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
    store.update_bed_count_for_icu(user_id, next_bed_count)

    bed_count = store.get_bed_count_for_icu(icu_id)
    self.assertEqual(bed_count.n_covid_occ, 7)
    self.assertEqual(bed_count.n_covid_free, 6)
    self.assertEqual(bed_count.n_ncovid_occ, 8)
    self.assertEqual(bed_count.n_ncovid_free, 5)
    self.assertEqual(bed_count.n_covid_deaths, 4)
    self.assertEqual(bed_count.n_covid_healed, 3)
    self.assertEqual(bed_count.n_covid_refused, 2)
    self.assertEqual(bed_count.n_covid_transfered, 1)

  def test_get_visible_bed_counts_for_user(self):
    store = self.store
    admin_user_id = self.admin_user_id
    region_id1 = self.add_region("region1")
    region_id2 = self.add_region("region2")

    now = datetime.now()

    def add_icu(region_id, name, values):
      icu_id = store.add_icu(admin_user_id, ICU(name=name, region_id=region_id))
      for index, value in enumerate(values):
        store.update_bed_count_for_icu(
            admin_user_id,
            BedCount(
                icu_id=icu_id,
                n_covid_occ=value,
                create_date=now + timedelta(seconds=index)))
      return icu_id

    def get_values(user_id, max_date=None):
      bed_counts = store.get_visible_bed_counts_for_user(
          user_id, max_date=max_date)
      values = {}
      for bed_count in bed_counts:
        values[bed_count.icu.name] = bed_count.n_covid_occ
      return values

    icu_id1 = add_icu(region_id1, "icu1", [1, 2])
    icu_id2 = add_icu(region_id1, "icu2", [4, 3])
    icu_id3 = add_icu(region_id2, "icu3", [5])

    # Admin user should see bed counts of all ICUs.
    self.assertDictEqual(
        get_values(admin_user_id), {
            "icu1": 2,
            "icu2": 3,
            "icu3": 5
        })

    # Restrict to now + 1.
    self.assertDictEqual(
        get_values(admin_user_id, now + timedelta(seconds=1)), {
            "icu1": 1,
            "icu2": 4,
            "icu3": 5
        })

    # user1 can view ICU1 and 2 as they are in the same region and user1 is
    # assigned to ICU1.
    user_id1 = store.add_user_to_icu(admin_user_id, icu_id1, User(name="user1"))
    self.assertDictEqual(get_values(user_id1), {"icu1": 2, "icu2": 3})

    # user2 can only view ICU3.
    user_id2 = store.add_user_to_icu(admin_user_id, icu_id3, User(name="user2"))
    self.assertDictEqual(get_values(user_id2), {"icu3": 5})

  def test_create_store_for_sqlite_db(self):
    with tempfile.TemporaryDirectory() as tmp_folder:
      store = db_store.create_store_for_sqlite_db(
          os.path.join(tmp_folder, "test.db"))
