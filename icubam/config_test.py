from icubam import config


def test_read():
  TEST_CONFIG_PATH = 'resources/test.toml'
  mode = 'dev'
  cfg = config.Config(TEST_CONFIG_PATH, mode=mode)
  assert cfg.db.sqlite_path == ':memory:'
  assert cfg.server.port == 8888
  assert cfg.scheduler.max_retries == 3
