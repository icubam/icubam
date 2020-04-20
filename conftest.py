from pathlib import Path
from subprocess import call

import pytest
from icubam.config import Config


def pytest_addoption(parser):
  parser.addoption(
    "--runslow", action="store_true", default=False, help="run slow tests"
  )
  parser.addoption(
    "--icubam-config",
    action="store",
    default=None,
    help="Path to ICUBAM config for integration tests"
  )


@pytest.fixture(scope="session")
def integration_config(request, tmpdir_factory):
  config_path = request.config.getoption("--icubam-config")

  if config_path is None:
    pytest.skip('skipping integration tests as --icubam-config not provided.')
  config = Config(config_path)
  db_path = Path(config.db.sqlite_path)
  if not db_path.exists():
    pytest.skip(
      f'skipping integration tests as could not find DB at {db_path}.'
    )

  db_path_new = str(tmpdir_factory.mktemp('tmpdir_factory').join("icubam.db"))

  exit_code = call(['sqlite3', str(db_path), '.backup {db_path_new}'])
  if exit_code:
    raise ValueError('Could not make a temporary copy of the DB.')
  config.db.sqlite_path = db_path_new
  assert config.db.sqlite_path == db_path_new
  return config


def pytest_configure(config):
  config.addinivalue_line("markers", "slow: mark test as slow to run")
  config.addinivalue_line(
    "markers", "integration: mark tests as integration test"
  )


def pytest_collection_modifyitems(config, items):
  if config.getoption("--runslow"):
    # --runslow given in cli: do not skip slow tests
    return
  skip_slow = pytest.mark.skip(reason="need --runslow option to run")
  for item in items:
    if "slow" in item.keywords:
      item.add_marker(skip_slow)
