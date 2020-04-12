import itertools

import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd

from ..data import BEDCOUNT_COLUMNS, ICU_NAMES_GRAND_EST
from ..plot import DEPARTMENT_GRAND_EST_COLOR, plot_int

data_source = "all_data"


def plot(data):
  data = data.loc[data.icu_name.isin(ICU_NAMES_GRAND_EST)]
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  data = data.groupby(["date", "department"]).agg(agg)
  data = data.reset_index()
  data["pct_occ"] = (
    data["n_covid_occ"] / (data["n_covid_occ"] + data["n_covid_free"])
  ).fillna(0)

  fig, ax = plt.subplots(1, figsize=(7, 4))
  date_idx_range = np.arange(len(data.date.unique()))
  for department, d in data.groupby("department"):
    d = d.sort_values(by="date")
    plot_int(
      date_idx_range,
      d["pct_occ"],
      ax=ax,
      color=DEPARTMENT_GRAND_EST_COLOR[department],
      label=department,
      lw=2,
    )
  ge_pct_occ = data.groupby("date").pct_occ.mean().sort_index().values
  plot_int(
    date_idx_range,
    ge_pct_occ,
    ax=ax,
    color="k",
    marker=False,
    label="Grand Est",
    lw=4,
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
        facecolor=DEPARTMENT_GRAND_EST_COLOR[department],
        label=department,
        linewidth=3,
      ) for department in sorted(data.department.unique())
    ] + [
      matplotlib.patches.Patch(
        facecolor="k",
        label="Grand Est",
        linewidth=3,
      )
    ],
    loc="lower right",
  )
  ax.set_ylabel("Pourcentage d'occupations des lits Covid+")

  tikzplotlib_kwargs = dict(
    axis_width="14cm",
    axis_height="8cm",
  )
  return fig, tikzplotlib_kwargs
