import unittest

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
