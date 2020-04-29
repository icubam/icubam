import unittest
import pickle

from icubam import config


class ConfigTestCase(unittest.TestCase):
  TEST_CONFIG_PATH = 'resources/test.toml'

  def setUp(self):
    super().setUp()
    self.config = config.Config(self.TEST_CONFIG_PATH)

  def test_read(self):
    self.assertEqual(self.config.db.sqlite_path, ':memory:')
    self.assertEqual(self.config.server.port, 8888)
    self.assertEqual(self.config.scheduler.max_retries, 3)

  def test_missing_key(self):
    with self.assertRaises(AttributeError):
      self.config.invalid
    with self.assertRaises(KeyError):
      self.config['invalid']

  def test_pickle(self):
    """Check that config is picklable"""
    obj = pickle.dumps(self.config)
    config2 = pickle.loads(obj)
    self.assertEqual(self.config.db.sqlite_path, config2.db.sqlite_path)
    self.assertEqual(self.config.server.port, config2.server.port)
