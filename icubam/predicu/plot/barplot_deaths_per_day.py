import datetime

import matplotlib.gridspec
import matplotlib.pyplot as plt
import matplotlib.style
import numpy as np
import pandas as pd
import seaborn as sns

import predicu.data

data_source = "all_data"


def plot(data):
    column = "n_covid_deaths"
    d = data
    d = d.loc[d.icu_name.isin(predicu.data.ICU_NAMES_GRAND_EST)]
    d = d.groupby(["date", "department"]).sum().reset_index()
    d = d.sort_values(by="date")
    fig, ax = plt.subplots(1, figsize=(20, 10))
    x = d.date.values
    y = (
        d.n_covid_deaths.values
        / d.department.apply(predicu.data.DEPARTMENT_POPULATION.get).values
        * 1e5
    )
    sns.barplot(x=x, y=y, ax=ax, capsize=0.2)
    ax.axvline(6.5, c="red", alpha=0.7, ls="dotted", lw=6.0)
    ax.set_xticklabels(
        [date.strftime("%d/%m") for date in d.date.unique()],
        rotation=45,
        fontdict={"fontsize": "x-small"},
    )
    ax.set_ylabel("Décès par 100,000 habitants")
    ax.set_xlabel(None)
    txt = ax.text(
        6.5, 3.5, "Début acquisition", fontsize="xx-large", color="red"
    )
    txt.set_horizontalalignment("right")
    txt = ax.text(6.5, 3.2, r"ICUBAM", fontsize="xx-large", color="red")
    txt.set_horizontalalignment("right")
    tikzplotlib_args = {"axis_width": "10cm"}
    return fig, tikzplotlib_args
