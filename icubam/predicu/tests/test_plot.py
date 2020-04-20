from pathlib import Path

import pytest
from sqlalchemy import create_engine

import icubam.db.store as db_store
from icubam.db.store import StoreFactory, to_pandas
from icubam.db.fake import populate_store_fake
from icubam.predicu.data import normalize_colum_names
from icubam.predicu.plot import PLOTS, generate_plots
from icubam.predicu.test_utils import load_test_data


def test_load_test_data():
  """Ensure consitency between test data used in plots and BD schema
  
  e.g. between load_test_data and db.get_bed_counts
  """
  # TODO: cache generation of in memory DB with fake data into a pytest fixture
  df = load_test_data()['bedcounts']

  # duplicate columns with "date"
  del df['datetime']

  store = StoreFactory(create_engine("sqlite:///:memory:")).create()
  populate_store_fake(store)
  df_db = to_pandas(store.get_bed_counts())
  df_db = normalize_colum_names(df_db, 'bedcounts')
  # All bedcount columns in tests data used for plots must belong to the DB schema
  missing_columns = set(df.columns).difference(df_db.columns)
  assert not missing_columns


def test_generate_plots_wrong_name():
  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    generate_plots(plots=["invalid2"])


@pytest.mark.parametrize("name", PLOTS)
def test_generate_plots(name, tmpdir):
  output_dir = str(tmpdir.mkdir("sub"))
  generate_plots(
    plots=[name],
    output_dir=output_dir,
    cached_data=load_test_data(),
  )
  if name == "flux_dept_lits_dept_visu_4panels":
    assert (Path(output_dir) / "flux-lits-dept-Ardennes.png").exists()
    assert (Path(output_dir) / "flux-lits-dept-Moselle.png").exists()
  else:
    assert (Path(output_dir) / (name + ".png")).exists()


@pytest.mark.integration
@pytest.mark.parametrize("name", PLOTS)
def test_integration_generate_plots(name, integration_config, tmpdir):
  store = db_store.create_store_factory_for_sqlite_db(integration_config
                                                      ).create()

  cached_data = load_test_data()
  cached_data['bedcounts'] = to_pandas(store.get_bed_counts())

  output_dir = str(tmpdir.mkdir("sub"))
  generate_plots(plots=[name], output_dir=output_dir, cached_data=cached_data)
  assert (Path(output_dir) / (name + ".png")).exists()
