import os
from pathlib import Path

import pandas as pd
import pytest

from .. import data as data_module
from ..data import (
  BASE_PATH, DATA_PATHS, DEPARTMENTS_GRAND_EST, ICU_NAMES_GRAND_EST,
  load_combined_bedcounts_public
)
from ..plot import PLOTS, generate_plots


def test_generate_plots_wrong_name():
  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    generate_plots(plots=["invalid2"])


def monkeypatch_data_load_fun(data_source, data, monkeypatch):
  def new_data_load_fun(*args, **kwargs):
    return data

  monkeypatch.setattr(data_module, f"load_{data_source}", new_data_load_fun)


@pytest.mark.parametrize("name", PLOTS)
def test_generate_plots(name, tmpdir, monkeypatch):
  output_dir = str(tmpdir.mkdir("sub"))
  test_public_path = os.path.join(BASE_PATH, "tests/data/public_data.h5")
  test_public = pd.read_hdf(test_public_path, 'values')
  monkeypatch_data_load_fun("public", test_public, monkeypatch)
  test_bedcounts = pd.read_hdf(
    os.path.join(
      BASE_PATH,
      "tests/data/fake_all_bedcounts_2020-04-08_16h41.h5",
    ), "values"
  )
  monkeypatch_data_load_fun("bedcounts", test_bedcounts, monkeypatch)
  monkeypatch_data_load_fun("icubam", test_bedcounts, monkeypatch)
  icu_names_grand_est = list(
    test_bedcounts.loc[test_bedcounts.department.isin(DEPARTMENTS_GRAND_EST)
                       ].icu_name.unique()
  )
  monkeypatch.setattr(data_module, "ICU_NAMES_GRAND_EST", icu_names_grand_est)
  generate_plots(
    plots=[name],
    output_dir=output_dir,
  )
  assert (Path(output_dir) / (name + ".png")).exists()
