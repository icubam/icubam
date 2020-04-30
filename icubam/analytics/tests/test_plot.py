from pathlib import Path

import pytest
import sqlalchemy

import icubam.db.store as db_store
from icubam.db.fake import populate_store_fake
from icubam.analytics.plots import PLOTS, generate_plots
from icubam.analytics.preprocessing import preprocess_bedcounts
from icubam.analytics import dataset


@pytest.fixture
def fake_db():
  store_factory = db_store.StoreFactory(
    sqlalchemy.create_engine("sqlite:///:memory:", echo=False)
  )
  db = store_factory.create()
  populate_store_fake(db)
  return db


def test_generate_plots_wrong_name():
  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    generate_plots(plots=["invalid2"], data={})


def check_generate_plots(name, db, output_dir):
  data = {}
  bc = dataset.load_bed_counts(db)
  data['bedcounts'] = preprocess_bedcounts(bc)
  assert data['bedcounts'].shape[0] > 0
  generate_plots(plots=[name], output_dir=output_dir, data=data)
  output_dir = Path(output_dir)
  if name == "barplot_flow_per":
    assert (output_dir / "National-CUM_FLOW_7D.png").exists()
  elif name == "lineplot_beds_per":
    assert (output_dir / 'National-LINE_BEDS_PER_14D_COVID.png').exists()
  else:
    raise ValueError


@pytest.mark.parametrize("name", PLOTS)
def test_fake_generate_plots(name, tmpdir, fake_db):
  output_dir = str(tmpdir.mkdir("out"))
  check_generate_plots(name, fake_db, output_dir)
  output_dir = Path(output_dir)
  if name == "barplot_flow_per":
    assert (output_dir / "region_id=1-Paris-CUM_FLOW.png").exists()
  elif name == "lineplot_beds_per":
    assert (output_dir / 'region_id=1-Paris-LINE_BEDS_PER_COVID.png').exists()
  else:
    raise ValueError


@pytest.mark.integration
@pytest.mark.parametrize("name", PLOTS)
def test_integration_generate_plots(name, integration_config, tmpdir):
  store = db_store.create_store_factory_for_sqlite_db(integration_config
                                                      ).create()
  output_dir = str(tmpdir.mkdir("out"))
  check_generate_plots(name, store, output_dir)
