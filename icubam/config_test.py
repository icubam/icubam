import unittest
from unittest import mock

from icubam import config


FAKE_KEY = 'SOMETHING_SOMETHING_123'
FAKE_ENV = 'fakenv'


class ConfigTestCase(unittest.TestCase):
  TEST_CONFIG_PATH = 'resources/test.toml'

  def test_read(self):
    mode = 'dev'
    cfg = config.Config(self.TEST_CONFIG_PATH, mode=mode)
    self.assertEqual(cfg.db.sqlite_path, 'test.db')
    self.assertEqual(cfg.server.port, 8888)
    self.assertEqual(cfg.scheduler.max_retries, 3)

  def test_set_env_found(self):
    with mock.patch.dict('os.environ', {FAKE_KEY: FAKE_ENV}):
      mode = 'dev'  # Trick so that it does not break at __init__ time.
      cfg = config.Config(self.TEST_CONFIG_PATH, mode=mode)
      cfg.mode = 'prod'

      self.assertEqual(cfg.mode, 'prod')
      cfg._set_env(FAKE_KEY)
      self.assertEqual(cfg[FAKE_KEY], FAKE_ENV)

  def test_set_env_prod_not_found(self):
    with self.assertRaises(ValueError):
      mode = 'prod'
      cfg = config.Config(self.TEST_CONFIG_PATH, mode=mode)
      cfg._set_env(FAKE_KEY)

  def test_set_env_dev_not_found(self):
    mode = 'dev'
    cfg = config.Config(self.TEST_CONFIG_PATH, mode=mode)
    cfg._set_env(FAKE_KEY)
    self.assertIsNotNone(cfg[FAKE_KEY])
