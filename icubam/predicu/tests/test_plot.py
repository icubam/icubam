from pathlib import Path

import pytest

from icubam.predicu.plot import PLOTS, generate_plots
from icubam.predicu.test_utils import load_test_data


def test_generate_plots_wrong_name():
  msg = "Unknown plot.* invalid2"
  with pytest.raises(ValueError, match=msg):
    generate_plots(plots=["invalid2"])


@pytest.mark.parametrize("name", PLOTS)
def test_generate_plots(name, tmpdir, monkeypatch):
  output_dir = str(tmpdir.mkdir("sub"))
  generate_plots(
    plots=[name],
    output_dir=output_dir,
    cached_data=load_test_data(),
  )
  assert (Path(output_dir) / (name + ".png")).exists()
