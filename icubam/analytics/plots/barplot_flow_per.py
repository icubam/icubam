import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import seaborn
import pandas as pd
import math

from datetime import datetime
from icubam.analytics.data import BEDCOUNT_COLUMNS
from icubam.analytics.plots import plot_int
from icubam.analytics.preprocessing import compute_flow_per_dpt

FIG_NAME = 'CUM_FLOW_DEPT'
data_source = ["bedcounts"]


def plot(data, **kwargs):
  """This function will run gen_plot over each group of elements.
  
  In this case it will run it once nationally grouping by region, and
  then for each region grouping by department.
  """
  kwargs['days_ago'] = 8
  regions = data['region'].unique()
  data = data.fillna(0)
  # departments = data['department'].unique()
  # breakpoint()
  if kwargs.get('days_ago', None):
    data = data[data['create_date'] >=
                (datetime.now() -
                 pd.Timedelta(f"{kwargs['days_ago']}D")).date()]
  figs = {}
  for region in regions:
    region_id = data[data['region'] == region]['region_id'].iloc[0]
    region_data = data[data['region'] == region]
    figs[f'region_id={region_id}-{region}-{FIG_NAME}'] = gen_plot(
      region_data, groupby='department', **kwargs
    )

  tikzplotlib_kwargs = dict(
    axis_width="14cm",
    axis_height="8cm",
  )
  return figs, tikzplotlib_kwargs


def draw_rect(ax, x, start, end, label, GROUP_COLORS, hatch=''):
  """Draws a single rectangle patch for a cumulative bar plot."""
  rect_patch = matplotlib.patches.Rectangle(
    xy=(x, start),
    width=1,
    height=abs(end),
    fill=True,
    linewidth=0.7,
    edgecolor="black",
    hatch=hatch,
    facecolor=GROUP_COLORS[label],
    label=label,
  )
  ax.add_patch(rect_patch)
  return ax


def gen_plot(data, groupby='department', **kwargs):
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  groups = sorted(data[groupby].unique())
  GROUP_COLORS = {
    dpt: seaborn.color_palette("colorblind", len(groups))[i]
    for i, dpt in enumerate(groups)
  }
  data = data.groupby(["date", groupby]).agg(agg)
  data = data.reset_index()
  data = compute_flow_per_dpt(data)
  # Get rid of the first day as it has edge weirdness:
  start_date = sorted(data['date'].unique())[0]
  data = data[data['date'] > start_date]

  # Set plotting to 'flow':
  col = 'flow'
  # Start plotting!
  fig, ax = plt.subplots(1, figsize=(7, 4))
  # Iterate over dates:
  for i, (date,
          d_date) in enumerate(data.sort_values(by="date").groupby("date")):
    # Group into negative counts and positive counts:
    neg_deps = d_date[d_date[col] < 0][['department',
                                        col]].sort_values('department')
    pos_deps = d_date[d_date[col] >= 0][['department',
                                         col]].sort_values('department')
    # Accumulate starting point
    start_cum = neg_deps[col].sum()
    # Plot negative values:
    for j, row in neg_deps.iterrows():
      ax = draw_rect(
        ax, i, start_cum, abs(row[col]), row['department'], GROUP_COLORS
      )
      start_cum += abs(row[col])
    # Now plot positive values:
    start_cum = 0
    for j, row in pos_deps.iterrows():
      ax = draw_rect(
        ax, i, start_cum, abs(row[col]), row['department'], GROUP_COLORS
      )
      start_cum += abs(row[col])

  # Set axis limits
  ax.set_xlim(0, len(data.date.unique()))
  y_min = data[data[col] < 0].groupby('date')[col].sum().min() - 1
  y_max = data[data[col] > 0].groupby('date')[col].sum().max() + 1
  if math.isnan(y_min):
    y_min = -1
  if math.isnan(y_max):
    y_max = 1
  print(y_min, y_max)
  ax.set_ylim(y_min, y_max)
  ax.legend(
    bbox_to_anchor=(1.35, 1),
    ncol=1,
    handles=[
      matplotlib.patches.Patch(
        facecolor=GROUP_COLORS[g],
        label=g,
        linewidth=3.5,
      ) for g in groups
    ],
  )
  # Set global plot params:
  ax.set_ylabel("Nbr. d'entrés en Réa")
  ax.set_xticks(np.arange(len(data.date.unique())) + 0.5)
  ax.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(data.date.unique())],
    rotation=45,
  )
  ax.grid(axis='y', linestyle='--')

  return fig
