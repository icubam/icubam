import os
from pathlib import Path

import pandas as pd
import pytest

from .. import data as data_module
from ..data import (
  BASE_PATH, DATA_PATHS, ICU_NAMES_GRAND_EST, load_combined_icubam_public
)
from ..plot import PLOTS, generate_plots


def test_generate_plots_wrong_name():
  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    generate_plots(plots=["invalid2"])


@pytest.mark.parametrize("name", PLOTS)
def test_generate_plots(name, tmpdir, monkeypatch):
  output_dir = str(tmpdir.mkdir("sub"))
  test_public_data_path = os.path.join(BASE_PATH, "tests/data/public_data.h5")
  test_public_data = pd.read_hdf(test_public_data_path, 'values')
  monkeypatch.setattr(
    data_module, "ICU_NAMES_GRAND_EST", ["a", "b", "c", "d", "e"]
  )
  monkeypatch.setitem(
    DATA_PATHS,
    "icubam",
    os.path.join(
      BASE_PATH,
      "tests/data/fake_all_bedcounts_2020-04-08_16h41.csv",
    ),
  )
  test_icubam_data = pd.read_csv(DATA_PATHS["icubam"], index_col=False)
  test_combined = load_combined_icubam_public(
    test_icubam_data, test_public_data
  )
  assert len(test_combined) > 0
  generate_plots(
    plots=[name],
    output_dir=output_dir,
    icubam_data=test_icubam_data,
    public_data=test_public_data,
  )
  assert (Path(output_dir) / (name + ".png")).exists()
