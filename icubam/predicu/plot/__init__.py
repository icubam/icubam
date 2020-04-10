import itertools
import logging
import os
from typing import List, Optional

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import scipy
import seaborn

from ..data import (
  BEDCOUNT_COLUMNS, DEPARTMENTS, DEPARTMENTS_GRAND_EST, load_all_data,
  load_combined_icubam_public, load_icubam_data
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
DEPARTMENT_GRAND_EST_COLOR = {
  dpt: seaborn.color_palette("colorblind", len(DEPARTMENTS_GRAND_EST))[i]
  for i, dpt in enumerate(DEPARTMENTS_GRAND_EST)
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


def plot(plot_name, data, **plot_args):
  plot_module = __import__(f"{plot_name}", globals(), locals(), ["plot"], 1)
  plot_fun = plot_module.plot
  data_source = plot_module.data_source
  matplotlib.use("agg")
  matplotlib.style.use(plot_args["matplotlib_style"])
  fig, tikzplotlib_kwargs = plot_fun(data=data[data_source].copy())
  output_type = plot_args["output_type"]
  if plot_args["output_type"] == "tex":
    output_path = os.path.join(plot_args["output_dir"], f"{plot_name}.tex")
    __import__("tikzplotlib").save(
      filepath=output_path,
      figure=fig,
      **tikzplotlib_kwargs,
      standalone=True,
    )
  elif output_type in ["png", "pdf"]:
    fig.savefig(
      os.path.join(plot_args["output_dir"], f"{plot_name}.{output_type}")
    )
  else:
    raise ValueError(f"Unknown output type: {output_type}")
  plt.close(fig)


def generate_plots(
  plots: Optional[List[str]] = None,
  matplotlib_style: str = "seaborn-whitegrid",
  api_key: Optional[str] = None,
  icubam_data: pd.DataFrame = None,
  output_type: str = "png",
  output_dir: str = "/tmp/",
):
  plots = sorted(plots)
  # Note: the default values here should match the defaults in CLI below.
  if plots is None:
    plots = PLOTS
  if not os.path.isdir(output_dir):
    logging.info("creating directory %s" % output_dir)
    os.makedirs(output_dir)
  plots_unknown = set(plots).difference(PLOTS)
  if plots_unknown:
    raise ValueError("Unknown plot(s): {}".format(", ".join(plots_unknown)))
  data = {}
  data["all_data"] = load_all_data(icubam_data=icubam_data, api_key=api_key)
  data["combined_icubam_public"] = load_combined_icubam_public(
    icubam_data=icubam_data, api_key=api_key
  )
  if icubam_data is None:
    data["icubam_data"] = load_icubam_data(api_key=api_key)
  else:
    data["icubam_data"] = icubam_data

  for name in sorted(plots):
    logging.info("generating plot %s in %s" % (name, output_dir))
    plot(
      name,
      data=data,
      matplotlib_style=matplotlib_style,
      output_dir=output_dir,
      output_type=output_type,
    )
