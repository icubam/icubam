from absl.testing import absltest
import datetime
from icubam import icu_tree
from icubam.db import store
from icubam import config


class ICUTreeTestCase(absltest.TestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    self.factory = store.create_store_factory_for_sqlite_db(self.config)
    self.db = self.factory.create()
    self.populate_db()

  def populate_db(self):
    self.admin_id = self.db.add_default_admin()
    r1 = self.db.add_region(self.admin_id, store.Region(name='IDF'))
    r2 = self.db.add_region(self.admin_id, store.Region(name='PACA'))

    self.db.add_icu(
      self.admin_id,
      store.ICU(
        name='icu1', region_id=r1, dept='75', city='Paris', telephone='+65123'
      )
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu2', region_id=r1, dept='75', city='Paris')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu3', region_id=r1, dept='92', city='Clamart')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu4', region_id=r1, dept='93', city='Bobigny')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu5', region_id=r1, dept='93', city='Saint-Denis')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu6', region_id=r1, dept='94', city='Vitry')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu7', region_id=r1, dept='94', city='Creteil')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu8', region_id=r1, dept='94', city='Creteil')
    )
    self.db.add_icu(
      self.admin_id,
      store.ICU(name='icu9', region_id=r2, dept='13', city='Marseille')
    )
    self.icus = self.db.get_icus()
    self.regions = self.db.get_regions()

    self.insert_time = datetime.datetime(2020, 4, 8, 11, 13)
    # Adding bedcounts: here we cheat a bit since we insert zeros counts
    # to have those bedcounts on the map and simplify the maths.
    for icu in self.icus:
      count = store.BedCount(icu_id=icu.icu_id, create_date=self.insert_time)
      self.db.update_bed_count_for_icu(self.admin_id, count)

  def test_get_next_level(self):
    tree = icu_tree.ICUTree(level='region')
    self.assertEqual(tree.get_next_level(), 'dept')
    tree = icu_tree.ICUTree(level='icu')
    self.assertIsNone(tree.get_next_level())

  def test_level_name(self):
    icu = self.icus[0]
    self.assertEqual(icu.region_id, self.regions[0].region_id)
    tree = icu_tree.ICUTree(level='region')
    self.assertEqual(tree.get_level_name(icu), self.regions[0].name)

  def test_as_dict(self):
    tree = icu_tree.ICUTree(level='region')
    tree.label = 'label'
    tree.occ = 12
    tree.free = 4
    node_dict = tree.as_dict()
    self.assertIsInstance(node_dict, dict)
    self.assertEqual(node_dict['free'], tree.free)

  def test_account_for_beds(self):
    tree = icu_tree.ICUTree()
    bd = store.BedCount(n_covid_occ=34, n_covid_free=6)
    tree.account_for_beds(bd)
    self.assertEqual(tree.total, 40)

  def test_set_basic_information(self):
    icu = self.icus[0]
    tree = icu_tree.ICUTree()
    tree.set_basic_information(icu)
    self.assertEqual(tree.label, icu.name)

  def test_add(self):
    example = self.icus[7]
    insert_time = self.insert_time + datetime.timedelta(seconds=1)
    self.db.update_bed_count_for_icu(
      self.admin_id,
      store.BedCount(
        icu_id=self.icus[1].icu_id,
        n_covid_occ=12,
        n_covid_free=4,
        create_date=insert_time
      )
    )
    self.db.update_bed_count_for_icu(
      self.admin_id,
      store.BedCount(
        icu_id=example.icu_id,
        n_covid_occ=1,
        n_covid_free=19,
        create_date=insert_time
      )
    )

    tree = icu_tree.ICUTree()
    icus = self.db.get_icus()
    bedcounts = self.db.get_latest_bed_counts()
    tree.add_many(icus, bedcounts)

    self.assertEqual(tree.level, 'country')
    self.assertGreater(len(tree.children), 0)
    self.assertIn(example.region.name, tree.children)
    self.assertEqual(tree.occ, 13)
    self.assertEqual(tree.free, 23)
    self.assertEqual(tree.total, 36)
    self.assertFalse(tree.is_leaf)

    idf = tree.children[example.region.name]
    self.assertEqual(len(idf.children), 4)
    self.assertFalse(idf.is_leaf)
    self.assertIn(example.dept, idf.children)

    vdm = idf.children[example.dept]
    self.assertEqual(len(vdm.children), 2)
    self.assertFalse(vdm.is_leaf)
    self.assertIn(example.city, vdm.children)

    creteil = vdm.children[example.city]
    self.assertEqual(len(creteil.children), 2)
    self.assertFalse(creteil.is_leaf)
    self.assertIn(example.name, creteil.children)

    icu8_node = creteil.children[example.name]
    self.assertTrue(icu8_node.is_leaf)
    self.assertEqual(icu8_node.total, 20)

  def test_get_leaves(self):
    tree = icu_tree.ICUTree()
    tree.add_many(self.icus, self.db.get_latest_bed_counts())
    nodes = tree.get_leaves()
    self.assertEqual(len(nodes), 9)

  def test_extract_below(self):
    tree = icu_tree.ICUTree()
    tree.add_many(self.icus, self.db.get_latest_bed_counts())
    level = 'dept'
    nodes = tree.extract_below(level)
    self.assertEqual(len(nodes), 5)
    self.assertIsInstance(nodes[0], tuple)
    self.assertEqual(nodes[0][0].level, level)
    self.assertFalse(nodes[0][0].is_leaf)
    self.assertIsInstance(nodes[0][1], list)
    self.assertTrue(nodes[0][1][0].is_leaf)


if __name__ == '__main__':
  absltest.main()
