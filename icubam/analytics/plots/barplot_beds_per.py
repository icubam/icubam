import matplotlib.pyplot as plt
import numpy as np
# import seaborn

from icubam.analytics import plots

data_source = ["bedcounts"]

FIG_NAME = 'BAR_BEDS_PER'


def plot(data, **kwargs):
  return {
    **plots.plot_each_region(
      data,
      gen_plot,
      col_prefix="n_covid",
      fig_name=f"{FIG_NAME}_14D_COVID",
      days_ago=15,
      **kwargs
    ),
    **plots.plot_each_region(
      data,
      gen_plot,
      col_prefix="n_covid",
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
  n_tot = n_occ + n_free

  covid_pos = '+' if col_prefix == "n_covid" else '-'
  fig, ax = plt.subplots(1, figsize=(12, 6))

  date_range_idx = np.arange(len(n_tot))

  tot_color = 'brown'
  occ_color = 'green'

  ax.set_ylabel('# Lits', color=tot_color)
  ax.tick_params(axis='y', labelcolor=tot_color)
  ax.bar(
    date_range_idx,
    n_tot,
    label=f'# lits réa COVID{covid_pos} (total)',
    color=tot_color,
    edgecolor=tot_color,
    lw=2,
    ls='-',
    alpha=0.2
  )
  ax.bar(
    date_range_idx,
    n_occ,
    label=f'# lits réa COVID{covid_pos} (occupés)',
    color=occ_color,
    edgecolor=None,
    lw=3,
    ls='-',
    alpha=0.8
  )
  ax.legend(
    handlelength=4,
    loc='best',
    frameon=True,
    facecolor='white',
    framealpha=0.8
  )
  #   ax.set_xticks(x_ticks_c)
  ax.set_ylim(bottom=0)

  ax.set_ylabel(r"Nombre de lits")
  ax.set_xticks(np.arange(data.date.unique().shape[0]))
  ax.set_xticklabels(
    [date.strftime("%d-%m") for date in sorted(data.date.unique())],
    rotation=45,
  )
  fig.tight_layout()
  return fig
