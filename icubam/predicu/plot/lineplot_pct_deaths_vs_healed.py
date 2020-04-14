import matplotlib.pyplot as plt
import numpy as np

from ..data import BEDCOUNT_COLUMNS, ICU_NAMES_GRAND_EST
from ..plot import (
  COL_COLOR, COLUMN_TO_HUMAN_READABLE, RANDOM_MARKERS, plot_int
)

data_source = "all_data"


def plot(data):
  data = data.loc[data.icu_name.isin(ICU_NAMES_GRAND_EST)]
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  data = data.groupby(["date"]).agg(agg)
  data = data.sort_index().reset_index()
  data["pct_deaths"] = data["n_covid_deaths"] / (
    data["n_covid_deaths"] + data["n_covid_healed"]
  )
  data["pct_healed"] = data["n_covid_healed"] / (
    data["n_covid_healed"] + data["n_covid_deaths"]
  )
  fig, ax = plt.subplots(1, figsize=(7, 4))
  for col in ["pct_deaths", "pct_healed"]:
    plot_int(
      np.arange(len(data)),
      data[col],
      ax=ax,
      color=COL_COLOR[col],
      label=COLUMN_TO_HUMAN_READABLE[col],
      marker=next(RANDOM_MARKERS),
      lw=2,
    )
  ax.set_xticks(np.arange(data.date.unique().shape[0]))
  ax.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(data.date.unique())],
    rotation=45,
  )
  ax.set_ylabel("Pourcentage")
  ax.legend()
  tikzplotlib_kwargs = dict(
    axis_width="14cm",
    axis_height="6cm",
  )
  return fig, tikzplotlib_kwargs
