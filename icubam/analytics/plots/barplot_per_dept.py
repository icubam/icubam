import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd

from datetime import datetime

from icubam.analytics.data import BEDCOUNT_COLUMNS
from icubam.analytics.plots import COL_COLOR, COLUMN_TO_HUMAN_READABLE

data_source = ["bedcounts"]


def plot(data, **kwargs):
  kwargs['days_ago'] = 5
  regions = data['region'].unique()
  # departments = data['department'].unique()
  # breakpoint()
  if kwargs.get('days_ago', None):
    data = data[data['create_date'] >=
                (datetime.now() -
                 pd.Timedelta(f"{kwargs['days_ago']}D")).date()]
  figs = {}
  for region in regions:
    region_data = data[data['region'] == region]
    figs[region] = gen_plot(region_data, groupby='department', **kwargs)

  tikzplotlib_kwargs = dict(
    axis_width="10cm",
    axis_height="10cm",
    textsize=5.0,
  )
  return figs, tikzplotlib_kwargs


def gen_plot(data, groupby="department", **kwargs):
  data = data.groupby(["date",
                       groupby]).agg({col: "sum"
                                      for col in BEDCOUNT_COLUMNS})
  data = data.reset_index()
  data = data.sort_values(by=[groupby, "date"])
  data = data.groupby(groupby).last()
  data = data.reset_index()
  barplot_columns = [
    "n_covid_deaths",
    "n_covid_healed",
    "n_covid_transfered",
    # "n_covid_refused",
    "n_covid_occ",
  ]
  data["total"] = data[barplot_columns].sum(axis=1)
  data = data.sort_values(by="total", ascending=False)

  fig, ax = plt.subplots(1, figsize=(8, 8))
  for i, (_, row) in enumerate(data.iterrows()):
    last_x = 0
    for col in barplot_columns:
      rect_patch = matplotlib.patches.Rectangle(
        xy=(last_x, i),
        width=row[col],
        height=1,
        fill=True,
        linewidth=0.7,
        edgecolor="black",
        facecolor=COL_COLOR[col],
        label=COLUMN_TO_HUMAN_READABLE[col],
      )
      last_x = last_x + row[col]
      ax.add_patch(rect_patch)
  ax.set_xlim(0, data[barplot_columns].sum(axis=1).max())
  ax.set_ylim(0, len(data))
  ax.set_yticks(np.arange(len(data)) + 0.5)
  ax.set_yticklabels(data.department)
  xticks = np.arange(0, data[barplot_columns].sum(axis=1).max(), 100)
  for xtick in xticks:
    ax.axvline(x=xtick, ls="dashed", c="k", alpha=0.2)
  ax.set_xticks(xticks)
  ax.legend(
    handles=[
      matplotlib.patches.Patch(
        facecolor=COL_COLOR[col],
        label=COLUMN_TO_HUMAN_READABLE[col],
      ) for col in barplot_columns
    ],
    loc="upper right",
  )
  # ax.set_title(r'Nbr de décès par réa (18 mars $\rightarrow$ 3 avril)')

  return fig
