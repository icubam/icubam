import os
from pathlib import Path

import pandas as pd
import pytest

import icubam.predicu.data
from icubam.predicu.data import BASE_PATH
from icubam.predicu.plot import PLOTS, generate_plots


def test_generate_plots_wrong_name():
  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    generate_plots(plots=["invalid2"])


def monkeypatch_data_load_fun(data_source, data, monkeypatch):
  def new_data_load_fun(*args, **kwargs):
    return data

  monkeypatch.setattr(
    icubam.predicu.data, f"load_{data_source}", new_data_load_fun
  )


@pytest.mark.parametrize("name", PLOTS)
def test_generate_plots(name, tmpdir, monkeypatch):
  output_dir = str(tmpdir.mkdir("sub"))
  test_public_path = os.path.join(BASE_PATH, "tests/data/public_data.csv")
  test_public = pd.read_csv(test_public_path, index_col=False)
  test_public['date'] = pd.to_datetime(test_public['date']).dt.date
  monkeypatch_data_load_fun("public", test_public, monkeypatch)
  test_bedcounts_path = os.path.join(BASE_PATH, "tests/data/bedcounts.csv")
  test_bedcounts = pd.read_csv(test_bedcounts_path, index_col=False)
  test_bedcounts['date'] = pd.to_datetime(test_bedcounts['date']).dt.date
  test_bedcounts['datetime'] = pd.to_datetime(test_bedcounts['datetime'])
  monkeypatch_data_load_fun("bedcounts", test_bedcounts, monkeypatch)
  monkeypatch_data_load_fun("icubam", test_bedcounts, monkeypatch)
  generate_plots(
    plots=[name],
    output_dir=output_dir,
  )
  assert (Path(output_dir) / (name + ".png")).exists()
