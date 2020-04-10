import matplotlib.gridspec
import matplotlib.pyplot as plt
import numpy as np

import predicu.data
import predicu.plot

data_source = "all_data"


def plot(data):
  n_rows = (
    len(predicu.data.CUM_COLUMNS) + len(predicu.data.CUM_COLUMNS) % 2
  ) // 2
  fig = plt.figure(figsize=(n_rows * 5, 10))
  gs = matplotlib.gridspec.GridSpec(n_rows, 2)
  ax0 = None
  for i, col in enumerate(predicu.data.CUM_COLUMNS):
    ax = fig.add_subplot(gs[i // 2, i % 2], sharex=ax0)
    if ax0 is None:
      ax0 = ax
    for g, d in data.groupby("department"):
      d = d.groupby("date")[col].sum().sort_index()
      ax.plot(np.arange(d.values.shape[0]), d.values, label=g)
    ax.set_title(predicu.plot.COLUMN_TO_HUMAN_READABLE[col])
    dates = sorted(list(data.date.unique()))
    ax.set_xticks(np.arange(d.values.shape[0]))
    ax.set_xticklabels(
      [date.strftime("%d/%m") for date in dates],
      rotation=45,
      fontdict={"fontsize": "x-small"},
    )
  ax0.legend(ncol=2, loc="upper left", frameon=True, fontsize="xx-small")
  fig.tight_layout()
  fig.subplots_adjust(hspace=0.2)
  tikzplotlib_kwargs = dict(
    extra_groupstyle_parameters={
      r"horizontal sep=0.2cm",
      r"vertical sep=3cm",
    }
  )
  return fig, tikzplotlib_kwargs
