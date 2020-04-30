import matplotlib.pyplot as plt
import numpy as np
import itertools

from icubam.analytics import plots

data_source = ["bedcounts"]

FIG_NAME = 'BAR_BEDS_PER'


def plot(data, **kwargs):
  all_plots = {}
  for col_prefix, n_days in itertools.product(('n_covid', 'n_ncovid'),
                                              (None, 14, 7)):
    covid_pos = '+' if col_prefix == 'n_covid' else '-'
    days = '' if n_days is None else f'{n_days}D_'
    all_plots.update(
      plots.plot_each_region(
        data,
        gen_plot,
        col_prefix=col_prefix,
        fig_name=f"{FIG_NAME}_{days}COVID{covid_pos}",
        **kwargs
      )
    )
  return all_plots


def gen_plot(
  data, groupby="department", col_prefix="n_covid", figsize=(12, 6), **kwargs
):
  n_occ = data.groupby("date").sum()[f"{col_prefix}_occ"]
  n_free = data.groupby("date").sum()[f"{col_prefix}_free"]
  n_tot = n_occ + n_free

  covid_pos = '+' if col_prefix == "n_covid" else '-'
  fig, ax = plt.subplots(1, figsize=figsize, constrained_layout=True)

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
  return fig
