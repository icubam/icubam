from absl.testing import absltest
from itertools import repeat
from sqlalchemy import create_engine
from icubam.db.fake import populate_store_fake
from icubam.db.wipe import wipe_db
from icubam.db.store import Store, StoreFactory


class WipeTest(absltest.TestCase):
  def setUp(self):
    self.engine = create_engine("sqlite:///:memory:", echo=False)
    store_factory = StoreFactory(self.engine)
    self.store = store_factory.create()
    populate_store_fake(self.store)

  def test_wipe(self):
    with self.engine.connect() as conn:
      wipe_db(conn.connection, keep_beds=False)
      users = list(self.store.get_users())
      self.assertItemsEqual([user.name for user in users],
                            repeat("Jean Dumont", len(users)))
      self.assertItemsEqual([user.email for user in users],
                            repeat("jean.dumont@example.org", len(users)))
      bed_counts = list(self.store.get_bed_counts(None))
      self.assertItemsEqual([bc.n_covid_free for bc in bed_counts],
                            repeat(2, len(bed_counts)))

  def test_keep_beds(self):
    with self.engine.connect() as conn:
      wipe_db(conn.connection, keep_beds=True)
      bed_counts = list(self.store.get_bed_counts(None))
      self.assertFalse(all([bc.n_covid_free == 2 for bc in bed_counts]))
