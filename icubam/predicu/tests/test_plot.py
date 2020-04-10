import os
from pathlib import Path

import pytest

import predicu.data
import predicu.plot


def test_generate_plots_wrong_name():

  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    predicu.plot.generate_plots(plots=["invalid2"])


@pytest.mark.parametrize("name", predicu.plot.PLOTS)
def test_generate_plots(name, tmpdir, monkeypatch):
  output_dir = str(tmpdir.mkdir("sub"))
  monkeypatch.setitem(
    predicu.data.DATA_PATHS,
    "icubam",
    os.path.join(
      predicu.data.BASE_PATH,
      "tests/data/fake_all_bedcounts_2020-04-08_16h41.csv",
    ),
  )
  predicu.plot.generate_plots(plots=[name], output_dir=output_dir)

  assert (Path(output_dir) / (name + ".png")).exists()
