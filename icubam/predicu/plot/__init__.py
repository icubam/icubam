import itertools
import logging
import os
from typing import Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import scipy
import seaborn

from icubam.predicu.data import (
  BEDCOUNT_COLUMNS, DEPARTMENTS, load_if_not_cached
)

COLUMN_TO_HUMAN_READABLE = {
  "n_covid_deaths": "Décès",
  "n_covid_healed": "Sorties de réa",
  "n_covid_transfered": "Transferts (autre réa)",
  "n_covid_refused": "Refus (faute de place)",
  "n_covid_free": "Lits Covid+ libres",
  "n_ncovid_free": "Lits Covid- libres",
  "n_covid_occ": "Lits Covid+ occupés",
  "n_ncovid_occ": "Lits Covid- occupés",
  "flow": "Flux total de patients",
  "pct_deaths": "Pourcentage de décès",
  "pct_healed": "Pourcentage de sorties",
}

COL_COLOR = {
  col: seaborn.color_palette("colorblind",
                             len(BEDCOUNT_COLUMNS) + 1)[i]
  for i, col in enumerate(BEDCOUNT_COLUMNS + ["flow"])
}
COL_COLOR.update({
  "n_covid_deaths": (0, 0, 0),
  "n_covid_healed": (
    0.00784313725490196,
    0.6196078431372549,
    0.45098039215686275,
  ),
  "n_covid_occ": (0.8, 0.47058823529411764, 0.7372549019607844),
  "n_covid_transfered": (
    0.00392156862745098,
    0.45098039215686275,
    0.6980392156862745,
  ),
  "n_covid_refused": (0.8352941176470589, 0.3686274509803922, 0.0),
  "pct_deaths": (0, 0, 0),
  "pct_healed": (
    0.00784313725490196,
    0.6196078431372549,
    0.45098039215686275,
  ),
})
DEPARTMENT_COLOR = {
  dpt: seaborn.color_palette("colorblind", len(DEPARTMENTS))[i]
  for i, dpt in enumerate(DEPARTMENTS)
}
RANDOM_MARKERS = itertools.cycle(("x", "+", ".", "|"))
RANDOM_COLORS = itertools.cycle(seaborn.color_palette("colorblind", 10))


def plot_int(
  x,
  y,
  ax,
  marker=None,
  label=None,
  color=None,
  lw=1.0,
  ls="solid",
  s=3,
  fill_below=False,
):
  f = scipy.interpolate.interp1d(x, y, kind="quadratic")
  x_i = np.linspace(0, len(x) - 1, len(x) * 5)
  y_i = f(x_i)
  if marker is not None:
    ax.scatter(x, y, marker=marker, color=color)
  if fill_below:
    ax.fill_between(x_i, np.zeros(len(y_i)), y_i, color=color, label=label)
    ax.plot(x_i, y_i, color="white", lw=1, ls="dashed", alpha=1.0)
  else:
    ax.plot(x_i, y_i, color=color, lw=lw, label=label, ls=ls)
  return ax


PLOTS = []
for path in os.listdir(os.path.dirname(__file__)):
  if path.endswith(".py") and any(
    path.startswith(prefix)
    for prefix in ["barplot", "lineplot", "scatterplot", "stackplot"]
  ):
    plot_name = path.rsplit(".", 1)[0]
    PLOTS.append(plot_name)


def plot(
  plot_name: str,
  cached_data: Dict[str, pd.DataFrame],
  output_dir: str,
  output_type: str,
  api_key: str,
  icubam_host: str,
  matplotlib_style: str,
  restrict_to_grand_est_region: Optional[str],
):
  plot_module = __import__(f"{plot_name}", globals(), locals(), ["plot"], 1)
  plot_fun = plot_module.plot
  data_source = plot_module.data_source
  cached_data[data_source] = load_if_not_cached(
    data_source,
    cached_data,
    api_key=api_key,
    icubam_host=icubam_host,
    restrict_to_grand_est_region=restrict_to_grand_est_region,
  )
  matplotlib.use("agg")
  matplotlib.style.use(matplotlib_style)
  fig, tikzplotlib_kwargs = plot_fun(data=cached_data[data_source].copy())
  if output_type == "tex":
    output_path = os.path.join(output_dir, f"{plot_name}.tex")
    __import__("tikzplotlib").save(
      filepath=output_path,
      figure=fig,
      **tikzplotlib_kwargs,
      standalone=True,
    )
  elif output_type in ["png", "pdf"]:
    fig.savefig(os.path.join(output_dir, f"{plot_name}.{output_type}"))
  else:
    raise ValueError(f"Unknown output type: {output_type}")
  plt.close(fig)


def generate_plots(
  plots: Optional[List[str]] = None,
  matplotlib_style: str = "seaborn-whitegrid",
  api_key: Optional[str] = None,
  icubam_host: Optional[str] = None,
  output_type: str = "png",
  output_dir: str = "/tmp",
  cached_data: Dict = None,
  restrict_to_grand_est_region: Optional[str] = False,
):
  if cached_data is None:
    cached_data = dict()
  if plots is None:
    plots = PLOTS
  plots = sorted(plots)
  if not os.path.isdir(output_dir):
    logging.info("creating directory %s" % output_dir)
    os.makedirs(output_dir)
  plots_unknown = set(plots).difference(PLOTS)
  if plots_unknown:
    raise ValueError("Unknown plot(s): {}".format(", ".join(plots_unknown)))
  for name in sorted(plots):
    logging.info("generating plot %s in %s" % (name, output_dir))
    plot(
      name,
      cached_data=cached_data,
      matplotlib_style=matplotlib_style,
      output_dir=output_dir,
      output_type=output_type,
      api_key=api_key,
      icubam_host=icubam_host,
      restrict_to_grand_est_region=restrict_to_grand_est_region,
    )
