import unittest
from icubam import config


class ConfigTestCase(unittest.TestCase):
  TEST_CONFIG_PATH = 'resources/test.toml'

  def test_read(self):
    os.
    cfg = config.Config(self.TEST_CONFIG_PATH)
    self.assertEqual(cfg.database.sqlite_db, 'test.db')
    self.assertEqual(cfg.database.sqlite_db, 'test.db')
