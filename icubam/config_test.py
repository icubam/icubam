import unittest

from icubam import config


class ConfigTestCase(unittest.TestCase):
  TEST_CONFIG_PATH = 'resources/test.toml'

  def test_read(self):
    mode = 'dev'
    cfg = config.Config(self.TEST_CONFIG_PATH, mode=mode)
    self.assertEqual(cfg.db.sqlite_path, 'test.db')
    self.assertEqual(cfg.server.port, 8888)
    self.assertEqual(cfg.scheduler.max_retries, 1)
