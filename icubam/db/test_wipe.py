from absl.testing import absltest
import itertools
from sqlalchemy import create_engine
from icubam.db.fake import populate_store_fake
from icubam.db.wipe import wipe_db
from icubam.db.store import StoreFactory


class WipeTest(absltest.TestCase):
  def wipe_close_and_reconnect(
    self,
    keep_beds=False,
    reset_admin=False,
    admin_email=None,
    admin_pass=None
  ):
    wipe_db(self.store, keep_beds, reset_admin, admin_email, admin_pass)
    self.store._session.close()
    self.store = self.store_factory.create()

  def setUp(self):
    self.store_factory = StoreFactory(
      create_engine("sqlite:///:memory:", echo=False)
    )
    self.store = self.store_factory.create()
    populate_store_fake(self.store)

  def test_wipe(self):
    self.wipe_close_and_reconnect(keep_beds=False)
    users = list(self.store.get_users())
    self.assertItemsEqual([user.name for user in users],
                          itertools.repeat("Jean Dumont", len(users)))
    self.assertItemsEqual([
      user.email for user in users
    ], itertools.repeat("jean.dumont@example.org", len(users)))
    bed_counts = list(self.store.get_bed_counts(None))
    self.assertItemsEqual([bc.n_covid_free for bc in bed_counts],
                          itertools.repeat(2, len(bed_counts)))

  def test_keep_beds(self):
    self.wipe_close_and_reconnect(keep_beds=True)
    users = list(self.store.get_users())
    self.assertItemsEqual([user.name for user in users],
                          itertools.repeat("Jean Dumont", len(users)))
    bed_counts = list(self.store.get_bed_counts(None))
    self.assertFalse(all([bc.n_covid_free == 2 for bc in bed_counts]))

  def test_reset_admin(self):
    email = "admin.test@example.org"
    self.wipe_close_and_reconnect(
      keep_beds=False,
      reset_admin=True,
      admin_email=email,
      admin_pass="f00b4r"
    )
    admins = list(self.store.get_admins())
    self.assertTrue(len(admins) == 1)
    self.assertTrue(admins[0].email == email)
