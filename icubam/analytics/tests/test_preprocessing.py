import numpy as np
import pytest
import sqlalchemy as sqla

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
