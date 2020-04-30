import numpy as np
import pytest
import pandas as pd
import sqlalchemy as sqla
from numpy.testing import assert_allclose

from icubam.analytics import dataset, preprocessing
from icubam.db import store
from icubam.db.fake import populate_store_fake


@pytest.fixture
def fake_db():
  store_factory = store.StoreFactory(
    sqla.create_engine("sqlite:///:memory:", echo=True)
  )
  db = store_factory.create()
  populate_store_fake(db)
  return db


def test_bedcounts_data_preprocessing(fake_db):
  data = dataset.load_bed_counts(fake_db)
  preprocessed = preprocessing.preprocess_bedcounts(data)
  assert len(preprocessed) > 0
  for icu_name, dg in preprocessed.groupby('icu_name'):
    dg = dg.sort_values(by='create_date')
    for col in dataset.CUM_COLUMNS:
      diffs = dg[col].diff(1).fillna(0).values
      assert np.all(diffs >= 0)


def test_enforce_daily_values_for_all_icus():
  df_raw = pd.DataFrame({
    "icu_name": ['A', 'B', 'A', 'A', 'A'],
    "department": ['D1', 'D2', 'D1', 'D1', 'D1'],
    "region": ['R1', 'R3', 'R1', 'R1', 'R1'],
    "n_covid_deaths": [0, 1, 2, 3, 5],
    "region_id": [1, 2, 1, 1, 1],
    "datetime":
    pd.to_datetime([
      '2020-01-01', '2020-01-02', '2020-01-02', '2020-01-03', '2020-01-04'
    ]),
    "create_date":
    pd.to_datetime([
      '2020-01-01', '2020-01-02', '2020-01-02', '2020-01-03', '2020-01-04'
    ]),
  })
  df_raw['date'] = df_raw["datetime"].dt.date
  for key in dataset.CUM_COLUMNS:
    df_raw[key] = [0, 1, 2, 3, 5]

  for key in dataset.NCUM_COLUMNS:
    df_raw[key] = [0, 3, 4, 2, 5]
  assert df_raw.shape == (5, 15)

  df = preprocessing.enforce_daily_values_for_all_icus(df_raw)
  assert set(df.columns) == set(df_raw.columns)
  assert df.shape == (8, 15)
  # For ICU A the data is unchanged
  assert_allclose(
    df.loc[df['icu_name'] == 'A', dataset.CUM_COLUMNS[0]].values, [0, 2, 3, 5]
  )
  assert_allclose(
    df.loc[df['icu_name'] == 'A', dataset.NCUM_COLUMNS[0]].values,
    [0, 4, 2, 5]
  )
  # For ICU B we fill missing days
  assert_allclose(
    df.loc[df['icu_name'] == 'B', dataset.CUM_COLUMNS[0]].values, [0, 1, 1, 1]
  )
  assert_allclose(
    df.loc[df['icu_name'] == 'B', dataset.NCUM_COLUMNS[0]].values,
    [0, 3, 3, 3]
  )
