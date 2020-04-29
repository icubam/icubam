import itertools
import logging

import numpy as np
import pandas as pd

from icubam.analytics import dataset

SPREAD_CUM_JUMPS_MAX_JUMP = {
  "n_covid_deaths": 10,
  "n_covid_transfered": 10,
  "n_covid_refused": 10,
  "n_covid_healed": 10,
}


def format_data(d: pd.DataFrame) -> pd.DataFrame:
  d["datetime"] = pd.to_datetime(d["create_date"])
  d["date"] = d["datetime"].dt.date
  d["department"] = d["icu_dept"]
  d["region"] = d["icu_region_name"]
  d["region_id"] = d["icu_region_id"]
  d = d[dataset.ALL_COLUMNS]
  return d


def preprocess_bedcounts(
  d: pd.DataFrame,
  spread_cum_jump_correction: bool = False,
  max_date: bool = None,
) -> pd.DataFrame:
  """This will process the bedcounts data to make analysis easier.

  There are five steps to the processing;
  1) Run a low-pass filter over all timeseries to remove single spikes that
     generally represent a data entry error.
  2) Aggregate the timeseries into their closest T-min intervals (T=15).
     This helps remove repeate updates, and takes the most recent update 
     for a T-min window, such that if there was a correction to bad data
     that will be the only value for that time window.
  3) Guarantee monotonicity on cumulative counts by replacing any decreasing
     values in the timeseries with their previous count: x_t = max(x_t, x_{t+1}).
  4) Imput missing data with two strategies: For holes > 3 days, impute data 
     by linearly interpolating between the two end-points of the missing set
     Subsequently, guarantee that each ICU has data for the whole timeseries,
     either by forward-propagating data at day t for impution, or setting to 0 for 
     days before the ICU started its data collection.
  5) (Optional) Spread out sudden jumps in data that reflect onboardings or
     change in reporting habit.
  
  Args:
    spread_cum_jump_correction : Whether to apply step 4) to the data.
    max_date : Only return data up to this date.
  """
  # Extract useful columns and recast date properly:
  d = format_data(d)
  d = d.fillna(0)

  if "Mulhouse-Chir" in d.icu_name.unique():
    d.loc[d.icu_name == "Mulhouse-Chir", "n_covid_healed"] = np.clip(
      (
        d.loc[d.icu_name == "Mulhouse-Chir", "n_covid_healed"] -
        d.loc[d.icu_name == "Mulhouse-Chir", "n_covid_transfered"]
      ).values,
      a_min=0,
      a_max=None,
    )
  icu_to_first_input_date = dict(
    d.groupby("icu_name")[["date"]].min().itertuples(name=None)
  )
  # Apply steps 1) 2) & 3)
  d = aggregate_multiple_inputs(d, "15Min")
  # Step 3)
  d = fill_in_missing_days(d, "3D")
  d = enforce_daily_values_for_all_icus(d)
  # Step 4)
  if spread_cum_jump_correction:
    d = spread_cum_jumps(d, icu_to_first_input_date)
  d = d[dataset.ALL_COLUMNS]
  d = d.sort_values(by=["date", "icu_name"])

  if max_date is not None:
    logging.info("data loaded's max date will be %s (excluded)" % max_date)
    d = d.loc[d.date < pd.to_datetime(max_date).date()]
  return d


def aggregate_multiple_inputs(d, agg_time_delta="15Min"):
  """Aggregate the timeseries into time bins.

  This will aggregate the timeseries into regular time intervals, and use the
  most recent update prior to time t to populate the bin at time t.
  """
  res_dfs = []
  for icu_name, dg in d.groupby("icu_name"):
    dg = dg.set_index("datetime")
    dg = dg.sort_index()
    td_diff = dg.index.to_series().diff(1)
    mask = td_diff > pd.Timedelta(agg_time_delta)
    mask = mask.shift(-1).fillna(True).astype(bool)
    dg = dg.loc[mask]

    # This will run low-pass filters to remove spurious outliers:
    # Rolling median average, 5 points (for cumulative qtities):
    # breakpoint()
    for col in dataset.CUM_COLUMNS:
      dg[col] = (
        dg[col].rolling(5, center=True, min_periods=1).median().astype(int)
      )

    # Rolling median average, 3 points (for non-cumulative qtities):
    for col in dataset.NCUM_COLUMNS:
      dg[col] = dg[col].fillna(0)
      dg[col] = (
        dg[col].rolling(3, center=True, min_periods=1).median().astype(int)
      )

    # Force cumulative columns to be monotonic by bringing any decreases in
    # the value up to their previous values i.e. x_t = max(x_t, x_{t-1}):
    for col in dataset.CUM_COLUMNS:
      new_col = []
      last_val = -100000
      for idx, row in dg.iterrows():
        if row[col] >= last_val:
          new_val = row[col]
        else:
          new_val = last_val
        new_col.append(new_val)
        last_val = new_val
      dg[col] = new_col

    res_dfs.append(dg.reset_index())
  return pd.concat(res_dfs)


def fill_in_missing_days(d, time_delta_threshold="3D"):
  """Group the timeseries into days, and impute data linearly for holes
     in the data superior to 3 days.
  """
  res_dfs = []

  for icu_name, dg in d.groupby("icu_name"):
    dg = dg.sort_values(by=["datetime"])
    time_delta = dg["datetime"].diff(1)
    for i, td in enumerate(time_delta):
      if td > pd.Timedelta(time_delta_threshold):
        n_days = td // pd.Timedelta("1D")
        val_init = dg.iloc[i - 1]
        val_final = dg.iloc[i]
        for added_day in range(n_days):
          added_datetime = (val_init.datetime + pd.Timedelta("1D") * added_day)
          added_date = val_init.date + pd.Timedelta("1D") * added_day
          new_row = {
            "datetime":
            added_datetime,
            "icu_name":
            val_init.icu_name,
            "date":
            added_date,
            "department":
            val_init.department,
            "n_covid_deaths":
            np.round(
              val_init.n_covid_deaths +
              (val_final.n_covid_deaths - val_init.n_covid_deaths) *
              added_day * 1.0 / n_days,
              4,
            ),
            "n_covid_healed":
            np.round(
              val_init.n_covid_healed +
              (val_final.n_covid_healed - val_init.n_covid_healed) *
              added_day * 1.0 / n_days,
              4,
            ),
            "n_covid_transfered":
            np.round(
              val_init.n_covid_transfered +
              (val_final.n_covid_transfered - val_init.n_covid_transfered) *
              added_day * 1.0 / n_days,
              4,
            ),
            "n_covid_refused":
            np.round(
              val_init.n_covid_refused +
              (val_final.n_covid_refused - val_init.n_covid_refused) *
              added_day * 1.0 / n_days,
              4,
            ),
            "n_covid_free":
            np.round(
              val_init.n_covid_free +
              (val_final.n_covid_free - val_init.n_covid_free) * added_day *
              1.0 / n_days,
              4,
            ),
            "n_ncovid_free":
            np.round(
              val_init.n_ncovid_free +
              (val_final.n_ncovid_free - val_init.n_ncovid_free) * added_day *
              1.0 / n_days,
              4,
            ),
            "n_covid_occ":
            np.round(
              val_init.n_covid_occ +
              (val_final.n_covid_occ - val_init.n_covid_occ) * added_day *
              1.0 / n_days,
              4,
            ),
            "n_ncovid_occ":
            np.round(
              val_init.n_ncovid_occ +
              (val_final.n_ncovid_occ - val_init.n_ncovid_occ) * added_day *
              1.0 / n_days,
              4,
            ),
          }
          dg = dg.append(pd.Series(new_row), ignore_index=True)
    dg = dg.sort_values(by=["datetime"])
    res_dfs.append(dg)
  return pd.concat(res_dfs)


def enforce_daily_values_for_all_icus(d):
  """Guarantee that each ICU has a continuous daily timeseries.
     
     Each missing day in the series is imputed by forward-filling from
     the most recent day with data.
  """
  dates = sorted(list(d.date.unique()))
  icu_names = sorted(list(d.icu_name.unique()))
  new_data_points = list()
  per_icu_prev_data_point = dict()
  icu_name_to_dept = dict(
    d.groupby(["icu_name", "department"]
              ).first().reset_index()[["icu_name", "department"
                                       ]].itertuples(name=None, index=False)
  )
  icu_name_to_region = dict(
    d.groupby(["icu_name", "region"]
              ).first().reset_index()[["icu_name", "region"
                                       ]].itertuples(name=None, index=False)
  )
  icu_name_to_region_id = dict(
    d.groupby(["icu_name", "region_id"]
              ).first().reset_index()[["icu_name", "region_id"
                                       ]].itertuples(name=None, index=False)
  )
  for date, icu_name in itertools.product(dates, icu_names):
    sd = d.loc[(d.date == date) & (d.icu_name == icu_name)]
    sd = sd.sort_values(by="datetime")
    new_data_point = {
      "date": date,
      "icu_name": icu_name,
      "department": icu_name_to_dept[icu_name],
      "region": icu_name_to_region[icu_name],
      "region_id": icu_name_to_region_id[icu_name],
      "datetime": date,
      "create_date": date,
    }
    new_data_point.update({col: 0 for col in dataset.CUM_COLUMNS})
    new_data_point.update({col: 0 for col in dataset.NCUM_COLUMNS})
    if icu_name in per_icu_prev_data_point:
      new_data_point.update({
        col: per_icu_prev_data_point[icu_name][col]
        for col in dataset.BEDCOUNT_COLUMNS
      })
    if len(sd) > 0:
      new_data_point.update({
        col: sd[col].iloc[-1]
        for col in dataset.BEDCOUNT_COLUMNS
      })
    per_icu_prev_data_point[icu_name] = new_data_point
    new_data_points.append(new_data_point)
  return pd.DataFrame(new_data_points)


def spread_cum_jumps(d, icu_to_first_input_date):
  assert np.all(d.date.values == d.datetime.values)
  # TODO: do not hardcode this value
  date_begin_transfered_refused = pd.to_datetime("2020-03-25").date()
  dfs = []
  for icu_name, dg in d.groupby("icu_name"):
    dg = dg.sort_values(by="date")
    dg = dg.reset_index()
    already_fixed_col = set()
    for switch_point, cols in (
      (icu_to_first_input_date[icu_name], dataset.CUM_COLUMNS),
      (
        date_begin_transfered_refused,
        ["n_covid_transfered", "n_covid_refused"],
      ),
    ):
      beg = max(
        dg.date.min(),
        switch_point - pd.Timedelta("2D"),
      )
      end = min(
        dg.date.max(),
        switch_point + pd.Timedelta("2D"),
      )
      for col in cols:
        if col in already_fixed_col:
          continue
        beg_val = dg.loc[dg.date == beg, col]
        if not len(beg_val):
          continue
        beg_val = beg_val.values[0]
        end_val = dg.loc[dg.date == end, col]
        if not len(end_val):
          continue
        end_val = end_val.values[0]
        diff = end_val - beg_val
        if diff >= SPREAD_CUM_JUMPS_MAX_JUMP[col]:
          spread_beg = dg.date.min()
          spread_end = end
          spread_range = pd.date_range(spread_beg, spread_end, freq="1D").date
          spread_value = diff // (spread_end - spread_beg).days
          remaining = diff % (spread_end - spread_beg).days
          dg.loc[dg.date.isin(spread_range), col] = np.clip(
            np.cumsum(np.repeat(spread_value, len(spread_range))),
            a_min=0,
            a_max=end_val,
          )
          dg.loc[dg.date == end, col] = np.clip(
            dg.loc[dg.date == end, col].values[0] + remaining,
            a_min=0,
            a_max=end_val,
          )
          already_fixed_col.add(col)
    dfs.append(dg)
  return pd.concat(dfs)


def compute_flow(d, col_prefix="n_covid"):
  sum_cols = set(dataset.CUM_COLUMNS +
                 [f"{col_prefix}_occ"]) - {f"{col_prefix}_refused"}
  summed = d[sum_cols].sum(axis=1)
  flow = summed.diff(1).fillna(0)
  flow.iloc[0] = summed.iloc[0]
  return flow


def compute_flow_per_dpt(data, groupby, col_prefix="n_covid"):
  dfs = []
  for dpt, d in data.groupby(groupby):
    d = d.sort_values(by="date")
    d["flow"] = compute_flow(d, col_prefix)
    d["cum_flow"] = d.flow.cumsum()
    dfs.append(d)
  return pd.concat(dfs)


PREPROCESSORS = {"bedcounts": preprocess_bedcounts}
