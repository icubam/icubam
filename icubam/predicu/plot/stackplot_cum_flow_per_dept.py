import matplotlib.cm
import matplotlib.gridspec
import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np

from icubam.predicu.data import BEDCOUNT_COLUMNS
from icubam.predicu.plot import DEPARTMENT_COLOR, plot_int
from icubam.predicu.flow import compute_flow_per_dpt

data_source = ["bedcounts"]


def plot(data):
  agg = {col: "sum" for col in BEDCOUNT_COLUMNS}
  data = data.groupby(["date", "department"]).agg(agg)
  data = data.reset_index()

  data = compute_flow_per_dpt(data)

  fig, ax = plt.subplots(1, figsize=(7, 4))

  date_idx_range = np.arange(len(data.date.unique()))
  sorted_depts = list(
    data.groupby("department").cum_flow.max().sort_values(
      ascending=False
    ).reset_index().department
  )
  for i, department in enumerate(sorted_depts):
    y = (
      data.loc[data.department.isin(
        sorted_depts[i:]
      )].groupby("date").flow.sum().sort_index().values
    )
    plot_int(
      date_idx_range,
      y,
      ax=ax,
      color=DEPARTMENT_COLOR[department],
      label=department,
      lw=1,
      fill_below=True,
    )
    if i == 0:
      plot_int(
        date_idx_range,
        y,
        ax=ax,
        color="black",
        label="Grand Est",
        lw=3,
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
        linewidth=3,
      ) for dpt in sorted_depts
    ] + [
      matplotlib.patches.Patch(
        facecolor="black",
        label="Grand Est",
        linewidth=1,
      )
    ],
    loc="upper left",
  )
  tikzplotlib_kwargs = dict(
    axis_width="14cm",
    axis_height="8cm",
  )
  return fig, tikzplotlib_kwargs
