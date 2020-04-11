import itertools

import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..data import ICU_NAMES_GRAND_EST, BEDCOUNT_COLUMNS
from ..plot import DEPARTMENT_GRAND_EST_COLOR, RANDOM_MARKERS, plot_int

data_source = "all_data"


def plot(data):
  data = data.loc[data.icu_name.isin(ICU_NAMES_GRAND_EST)]
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  data = data.groupby(["date", "department"]).agg(agg)
  data = data.reset_index()

  fig, ax = plt.subplots(1, figsize=(7, 4))
  date_idx_range = np.arange(len(data.date.unique()))
  for department, dg in data.groupby("department"):
    dg = dg.sort_values(by="date")
    y = dg.n_covid_occ  # + dg.n_covid_transfered.diff(1).fillna(0)
    plot_int(
      date_idx_range,
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
