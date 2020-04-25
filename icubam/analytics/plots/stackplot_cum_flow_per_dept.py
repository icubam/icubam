import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import seaborn
import pandas as pd

from datetime import datetime
from icubam.analytics.data import BEDCOUNT_COLUMNS
from icubam.analytics.plots import plot_int
from icubam.analytics.preprocessing import compute_flow_per_dpt

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
    figs[region] = plot_dept(data, region, groupby='department', **kwargs)

  tikzplotlib_kwargs = dict(
    axis_width="14cm",
    axis_height="8cm",
  )
  return figs, tikzplotlib_kwargs


def plot_dept(data, region, groupby='department', **kwargs):
  data = data[data['region'] == region]
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  groups = sorted(data[groupby].unique())
  DEPARTMENT_COLOR = {
    dpt: seaborn.color_palette("colorblind", len(groups))[i]
    for i, dpt in enumerate(groups)
  }
  data = data.groupby(["date", groupby]).agg(agg)
  data = data.reset_index()

  data = compute_flow_per_dpt(data)
  start_date = sorted(data['date'].unique())[0]
  data = data[data['date'] > start_date]
  # breakpoint()
  fig, ax = plt.subplots(1, figsize=(7, 4))

  date_idx_range = np.arange(len(data.date.unique()))
  sorted_groupby = list(
    data.groupby(groupby).cum_flow.max().sort_values(ascending=False
                                                     ).reset_index().department
  )
  for i, department in enumerate(sorted_groupby):
    y = (
      data.loc[data.department.isin(
        sorted_groupby[i:]
      )].groupby("date").flow.sum().sort_index().values
    )
    # ax.plot(date_idx_range, y, label=department)
    plot_int(
      date_idx_range,
      y,
      ax=ax,
      color=DEPARTMENT_COLOR[department],
      label=department,
      lw=0.5,
      fill_below=True,
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
        facecolor=DEPARTMENT_COLOR[dpt],
        label=dpt,
        linewidth=1.5,
      ) for dpt in sorted_groupby
    ] + [
      matplotlib.patches.Patch(
        facecolor="black",
        label="Grand Est",
        linewidth=1,
      )
    ],
    loc="upper left",
  )

  return fig
