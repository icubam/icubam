import datetime
import json

import matplotlib.gridspec
import matplotlib.lines
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import scipy.stats

from ..plot import DEPARTMENT_GRAND_EST_COLOR

data_source = "combined_bedcounts_public"


def plot(data):
  icubam_public_n_icu_patients_corr = (
    data.groupby("date")[[
      "n_icu_patients_icubam", "n_icu_patients_public"
    ]].corr().iloc[0::2, -1].reset_index().set_index("date").rename(
      columns={"n_icu_patients_public": "corr_icubam_public_n_icu_patients"}
    )
  )
  data = data.loc[data.date == data.date.max()]

  fig, ax = plt.subplots(1, figsize=(20, 10))

  x = data.loc[data.department != "Haut-Rhin"].department_pop
  y = data.loc[data.department != "Haut-Rhin"].n_hospitalised_patients
  slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
  slope, _, _, _ = np.linalg.lstsq(x[:, np.newaxis], y, rcond=None)
  x = np.linspace(0, x.max(), 100)
  y = slope[0] * x
  x = x[y >= 0]
  y = y[y >= 0]
  ax.plot(x, y, lw=3, ls="dashed", color="black", alpha=0.4)

  ax.set_xlim(0, data.department_pop.max() * 1.1)
  ax.set_ylim(0, 1200)

  for _, row in data.iterrows():
    scale = 3 * row.department_pop / data.department_pop.max()
    width = 0.02 * scale * ax.get_xlim()[1]
    height = 0.02 * scale * ax.get_ylim()[1]
    xy = (row.department_pop, row.n_hospitalised_patients)
    color = DEPARTMENT_GRAND_EST_COLOR[row.department]
    ax.add_artist(
      matplotlib.patches.Ellipse(
        xy=xy,
        width=width,
        height=height,
        facecolor=color + (0.2, ),
        zorder=2,
      )
    )
    ax.add_artist(
      matplotlib.patches.Ellipse(
        xy=xy,
        width=width,
        height=height,
        facecolor=(0, 0, 0, 0),
        edgecolor=color + (1.0, ),
        lw=3,
        zorder=2,
      )
    )

  dept_name_pos = {
    "Bas-Rhin": "below",
    "Haut-Rhin": "above",
    "Ardennes": "below",
    "Meuse": "above",
    "Haute-Marne": "below",
    "Aube": "below",
    "Moselle": "above",
  }

  for _, row in data.iterrows():
    x = row.department_pop + 10000
    y = row.n_hospitalised_patients
    ha = "left"
    if row.department in dept_name_pos:
      if dept_name_pos[row.department] == "above":
        x = row.department_pop
        y = row.n_hospitalised_patients + 50
        ha = "center"
      elif dept_name_pos[row.department] == "left":
        x = row.department_pop - 10000
        ha = "right"
      elif dept_name_pos[row.department] == "below":
        x = row.department_pop
        y = row.n_hospitalised_patients - 50
        ha = "center"
    text = ax.text(x, y, row.department)
    text.set_horizontalalignment(ha)
  ax.set_ylabel("Patients hospitalisés (total)")
  ax.set_xlabel("Habitants départementaux")
  ax.legend()
  tikzplotlib_kwargs = dict(
    axis_width="10cm",
    axis_height="10cm",
    textsize=7.0,
  )
  return fig, tikzplotlib_kwargs
