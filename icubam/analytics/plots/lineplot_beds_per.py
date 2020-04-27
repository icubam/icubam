import matplotlib.pyplot as plt
import numpy as np
# import seaborn

from icubam.analytics import plots

data_source = ["bedcounts"]

FIG_NAME = 'LINE_BEDS_PER'


def plot(data, **kwargs):
  return {
    **plots.plot_each_region(
      data,
      gen_plot,
      col_prefix="n_ncovid",
      fig_name=f"{FIG_NAME}_14D_COVID",
      days_ago=15,
      **kwargs
    ),
    **plots.plot_each_region(
      data,
      gen_plot,
      col_prefix="n_ncovid",
      fig_name=f"{FIG_NAME}_COVID",
      **kwargs
    ),
    **plots.plot_each_region(
      data,
      gen_plot,
      col_prefix="n_ncovid",
      fig_name=f"{FIG_NAME}_14D_NCOVID",
      days_ago=15,
      **kwargs
    ),
    **plots.plot_each_region(
      data,
      gen_plot,
      col_prefix="n_ncovid",
      fig_name=f"{FIG_NAME}_NCOVID",
      **kwargs
    )
  }



def gen_plot(data, groupby="department", col_prefix="n_covid", **kwargs):
  n_occ = data.groupby("date").sum()[f"{col_prefix}_occ"]
  n_free = data.groupby("date").sum()[f"{col_prefix}_free"]
  n_transfered = (
    data.groupby("date").sum()["n_covid_transfered"].diff(1).fillna(0)
  )
  n_tot = n_occ + n_free
  n_req = n_occ + n_transfered
  fig, ax = plt.subplots(1, figsize=(12, 6))

  date_range_idx = np.arange(len(n_req))

  ax = plots.plot_int(
    date_range_idx,
    n_tot.values,
    ax=ax,
    color=next(plots.RANDOM_COLORS),
    marker=next(plots.RANDOM_MARKERS),
    label="Total (lits)",
    lw=2,
  )
  ax = plots.plot_int(
    date_range_idx,
    n_req.values,
    ax=ax,
    color=next(plots.RANDOM_COLORS),
    marker=next(plots.RANDOM_MARKERS),
    label="Lits occupés + transferts",
    lw=2,
  )
  ax = plots.plot_int(
    date_range_idx,
    n_occ.values,
    ax=ax,
    color=next(plots.RANDOM_COLORS),
    marker=next(plots.RANDOM_MARKERS),
    label="Lits occupés",
    lw=2,
  )
  ax.set_ylabel(r"Nombre de lits")
  ax.legend(loc="lower right")
  ax.set_xticks(np.arange(data.date.unique().shape[0]))
  ax.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(data.date.unique())],
    rotation=45,
  )
  return fig
