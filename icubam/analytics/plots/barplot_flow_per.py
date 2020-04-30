import math

import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import seaborn

from icubam.analytics import plots
from icubam.analytics import dataset
from icubam.analytics.preprocessing import compute_flow_per_dpt

FIG_NAME = 'CUM_FLOW'
data_source = ["bedcounts"]


def plot(data, **kwargs):
  return {
    **plots.plot_each_region(
      data, gen_plot, f"{FIG_NAME}_14D", days_ago=15, **kwargs
    ),
    **plots.plot_each_region(data, gen_plot, FIG_NAME, **kwargs)
  }


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


def gen_plot(data, groupby='department', figsize=(7, 4), **kwargs):
  agg = {col: "sum" for col in dataset.BEDCOUNT_COLUMNS}
  groups = sorted(data[groupby].unique())
  GROUP_COLORS = {
    dpt: seaborn.color_palette("colorblind", len(groups))[i]
    for i, dpt in enumerate(groups)
  }
  data = data.groupby(["date", groupby]).agg(agg)
  data = data.reset_index()
  data = compute_flow_per_dpt(data, groupby)
  # Get rid of the first day as it has edge weirdness:
  start_date = sorted(data['date'].unique())[0]
  data = data[data['date'] > start_date]

  # Set plotting to 'flow':
  col = 'flow'
  # Start plotting!
  fig, ax = plt.subplots(1, figsize=figsize, constrained_layout=True)
  # Iterate over dates:
  for i, (date,
          d_date) in enumerate(data.sort_values(by="date").groupby("date")):
    # Group into negative counts and positive counts:
    neg_deps = d_date[d_date[col] < 0][[groupby, col]].sort_values(groupby)
    pos_deps = d_date[d_date[col] >= 0][[groupby, col]].sort_values(groupby)
    # Accumulate starting point
    start_cum = neg_deps[col].sum()
    # Plot negative values:
    for j, row in neg_deps.iterrows():
      ax = draw_rect(
        ax, i, start_cum, abs(row[col]), row[groupby], GROUP_COLORS
      )
      start_cum += abs(row[col])
    # Now plot positive values:
    start_cum = 0
    for j, row in pos_deps.iterrows():
      ax = draw_rect(
        ax, i, start_cum, abs(row[col]), row[groupby], GROUP_COLORS
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
