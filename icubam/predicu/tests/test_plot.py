from pathlib import Path

import pytest

import icubam.db.store as db_store
from icubam.db.store import to_pandas
from icubam.predicu.plot import PLOTS, generate_plots
from icubam.predicu.test_utils import load_test_data


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
