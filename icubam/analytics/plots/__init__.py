import itertools
import logging
import os
from typing import Dict, List

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import scipy
import seaborn

from icubam.predicu.data import BEDCOUNT_COLUMNS

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
  if path.endswith(".py") and path != "__init__.py":
    plot_name = path.rsplit(".", 1)[0]
    PLOTS.append(plot_name)


def plot(
  plot_name: str,
  plot_data: Dict[str, pd.DataFrame],
  output_type: str = "png",
  output_dir: str = "/tmp",
  matplotlib_style: str = "seaborn-whitegrid",
  **kwargs
):
  """Generate one plot

  Args:
    plot_name: name of the plot to make. Must match one of the files in plot/
    cached_data : a dictionary with **raw** data for different sources.
  """
  plot_module = __import__(plot_name, globals(), locals(), ["plot"], 1)
  plot_fun = plot_module.plot  # type: ignore

  data_source = plot_module.data_source.copy()  # type: ignore
  if len(data_source) == 1:
    plot_data = plot_data[data_source[0]]

  matplotlib.use("agg")
  matplotlib.style.use(matplotlib_style)
  figs, tikzplotlib_kwargs = plot_fun(data=plot_data, **kwargs)

  if not isinstance(figs, dict):
    figs = {f"{plot_name}.{output_type}": figs}
  for fname_out, fig in figs.items():
    if output_type in ["png", "pdf"]:
      fig.savefig(os.path.join(output_dir, fname_out), dpi=150)
    else:
      raise ValueError(f"Unknown output type: {output_type}")
    plt.close(fig)


def generate_plots(
  plots: List[str],
  data: Dict[str, pd.DataFrame],
  output_type: str = "png",
  output_dir: str = "/tmp",
  matplotlib_style: str = "seaborn-whitegrid",
  **kwargs
):
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
      plot_name=name,
      plot_data=data,
      output_type=output_type,
      output_dir=output_dir,
    )
