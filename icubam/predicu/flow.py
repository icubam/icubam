import pandas as pd

import predicu.data


def compute_flow(d):
    sum_cols = set(predicu.data.CUM_COLUMNS + ["n_covid_occ"]) - {
        "n_covid_refused"
    }
    summed = d[sum_cols].sum(axis=1)
    flow = summed.diff(1).fillna(0)
    flow.iloc[0] = summed.iloc[0]
    return flow


def compute_flow_per_dpt(data):
    dfs = []
    for dpt, d in data.groupby("department"):
        d = d.sort_values(by="date")
        d["flow"] = compute_flow(d)
        d["cum_flow"] = d.flow.cumsum()
        dfs.append(d)
    return pd.concat(dfs)
