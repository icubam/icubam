import os

import pandas as pd

from icubam.predicu.data import BASE_PATH


def load_test_data():
  test_public_path = os.path.join(BASE_PATH, "tests/data/public_data.csv")
  test_public = pd.read_csv(test_public_path, index_col=False)
  test_public['date'] = pd.to_datetime(test_public['date']).dt.date
  test_bc_path = os.path.join(BASE_PATH, "tests/data/bedcounts.csv")
  test_bc = pd.read_csv(test_bc_path, index_col=False, comment="#")
  test_bc['date'] = pd.to_datetime(test_bc['date']).dt.date
  test_bc['datetime'] = pd.to_datetime(test_bc['datetime'])
  cached_data = {
    "public": test_public,
    "bedcounts": test_bc,
    "icubam": test_bc,
  }
  return cached_data
