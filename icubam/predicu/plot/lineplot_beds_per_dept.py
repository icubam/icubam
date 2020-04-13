import itertools

import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from icubam.predicu.data import BEDCOUNT_COLUMNS
from icubam.predicu.plot import DEPARTMENT_GRAND_EST_COLOR, RANDOM_MARKERS, plot_int

data_source = "bedcounts"


def plot(data):
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  data = data.groupby(["date", "department"]).agg(agg)
  data = data.reset_index()

  fig, ax = plt.subplots(1, figsize=(7, 4))
  for department, dg in data.groupby("department"):
    dg = dg.sort_values(by="date")
    x = np.arange(len(dg))
    y = dg.n_covid_occ.values  # + dg.n_covid_transfered.diff(1).fillna(0)
    plot_int(
      x,
      y,
      ax=ax,
      color=DEPARTMENT_GRAND_EST_COLOR[department],
      label=department,
      lw=2,
      marker=next(RANDOM_MARKERS),
    )

  ax.set_xticks(np.arange(data.date.unique().shape[0]))
  ax.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(data.date.unique())],
    rotation=45,
  )
  ax.legend(
    ncol=2,
    handles=[
      matplotlib.patches.Patch(
        facecolor=DEPARTMENT_GRAND_EST_COLOR[dpt],
        label=dpt,
        linewidth=3,
      ) for dpt in sorted(data.department.unique())
    ],
    loc="upper left",
  )
  ax.set_ylabel(r"Somme lits occ. + transferts")
  tikzplotlib_kwargs = dict(
    axis_width="15cm",
    axis_height="8cm",
  )
  return fig, tikzplotlib_kwargs
