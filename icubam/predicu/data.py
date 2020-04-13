import itertools
import json
import logging
import os
import pickle
import urllib.request
from typing import Dict

import numpy as np
import pandas as pd
from lxml import html

BASE_PATH = os.path.dirname(__file__)

DATA_SOURCES = {
  "icubam", "bedcounts", "public", "combined_bedcounts_public"
}

DATA_PATHS = {
  "icu_name_to_department": "data/icu_name_to_department.json",
  "department_population": "data/department_population.csv",
  "departments": "data/france_departments.json",
}

for key, path in DATA_PATHS.items():
  DATA_PATHS[key] = os.path.join(BASE_PATH, path)

CUM_COLUMNS = [
  "n_covid_deaths",
  "n_covid_healed",
  "n_covid_transfered",
  "n_covid_refused",
]
NCUM_COLUMNS = [
  "n_covid_free",
  "n_ncovid_free",
  "n_covid_occ",
  "n_ncovid_occ",
]
BEDCOUNT_COLUMNS = CUM_COLUMNS + NCUM_COLUMNS
ALL_COLUMNS = (["icu_name", "date", "datetime", "department"] + CUM_COLUMNS +
               NCUM_COLUMNS)
SPREAD_CUM_JUMPS_MAX_JUMP = {
  "n_covid_deaths": 10,
  "n_covid_transfered": 10,
  "n_covid_refused": 10,
  "n_covid_healed": 10,
}


def load_if_not_cached(data_source, cached_data, **kwargs):
  if data_source not in DATA_SOURCES:
    raise ValueError(f"Unknown data source: {data_source}")
  load_data_fun = globals().get(f"load_{data_source}", None)
  if load_data_fun is None:
    raise RuntimeError(
      f"No loading function associated to data source {data_source}"
    )
  if cached_data is None or data_source not in cached_data:
    return load_data_fun(cached_data=cached_data, **kwargs)
  return cached_data[data_source]


def load_bedcounts(
  clean=True,
  spread_cum_jump_correction=False,
  api_key=None,
  icubam_host=None,
  max_date=None,
  cached_data=None,
):
  d = load_if_not_cached("icubam", cached_data, api_key=api_key,
                         icubam_host=icubam_host)
  if clean:
    d = clean_data(d, spread_cum_jump_correction)
  d = d.sort_values(by=["date", "icu_name"])
  if max_date is not None:
    logging.info("data loaded's max date will be %s (excluded)" % max_date)
    d = d.loc[d.date < pd.to_datetime(max_date).date()]
  return d


def load_icubam(cached_data=None, api_key=None, icubam_host=None):
  if api_key is None or icubam_host is None:
    raise RuntimeError("Provide API key to download ICUBAM data")
  else:
    protocol = "http" if icubam_host.startswith("localhost") else "https"
    url = (
      f"{protocol}://{icubam_host}/"
      f"db/all_bedcounts?format=csv&API_KEY={api_key}"
    )
    logging.info("downloading data from %s" % url)
    d = pd.read_csv(url.format(api_key))
  icu_name_to_department = load_icu_name_to_department()
  icu_name_to_department.update(
    dict(d[["icu_name", "icu_dept"]].itertuples(name=None, index=False))
  )
  logging.info("updating %s" % DATA_PATHS["icu_name_to_department"])
  with open(DATA_PATHS["icu_name_to_department"], "w") as f:
    json.dump(icu_name_to_department, f)
  d = d.rename(columns={"create_date": "date"})
  d = format_data(d, icu_name_to_department)
  return d


def load_pre_icubam(data_path, cached_data=None):
  d = load_data_file(data_path)
  d = d.rename(
    columns={
      "Hopital": "icu_name",
      "NbSortieVivant": "n_covid_healed",
      "NbCOVID": "n_covid_occ",
      "NbLitDispo": "n_covid_free",
      "NbDeces": "n_covid_deaths",
      "Date": "date",
    }
  )
  fix_icu_names = {
    "C-Scweitzer": "C-Schweitzer",
    "Bezannes": "C-Bezannes",
    "NHC-Chir": "NHC-ChirC",
  }
  for wrong_name, fixed_name in fix_icu_names.items():
    d.loc[d.icu_name == wrong_name, "icu_name"] = fixed_name
  fix_same_icu = {
    "CHR-SSPI": "CHR-Thionville",
    "CHR-CCV": "CHR-Thionville",
    "Nancy-NC": "Nancy-RCP",
  }
  for old, new in fix_same_icu.items():
    d.loc[d.icu_name == old, "icu_name"] = new
  missing_columns = [
    "n_covid_transfered",
    "n_covid_refused",
    "n_ncovid_free",
    "n_ncovid_occ",
  ]
  for col in missing_columns:
    d[col] = 0
  d = format_data(d, load_icu_name_to_department())
  return d


def format_data(d, icu_name_to_department):
  d["datetime"] = pd.to_datetime(d["date"])
  d["date"] = d["datetime"].dt.date
  d["department"] = d.icu_name.apply(icu_name_to_department.get)
  d = d[ALL_COLUMNS]
  return d


def clean_data(d, spread_cum_jump_correction=False):
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
  d = aggregate_multiple_inputs(d)
  # d = fix_noncum_inputs(d)
  d = get_clean_daily_values(d)
  if spread_cum_jump_correction:
    d = spread_cum_jumps(d, icu_to_first_input_date)
  d = d[ALL_COLUMNS]
  return d


def aggregate_multiple_inputs(d):
  res_dfs = []
  for icu_name, dg in d.groupby("icu_name"):
    dg = dg.set_index("datetime")
    dg = dg.sort_index()
    mask = ((dg.index.to_series().diff(1) >
             pd.Timedelta("15Min")).shift(-1).fillna(True).astype(bool))
    dg = dg.loc[mask]

    for col in CUM_COLUMNS:
      dg[col] = (
        dg[col].rolling(5, center=True, min_periods=1).median().astype(int)
      )

    for col in NCUM_COLUMNS:
      dg[col] = dg[col].fillna(0)
      dg[col] = (
        dg[col].rolling(3, center=True, min_periods=1).median().astype(int)
      )

    for col in CUM_COLUMNS:
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


def get_clean_daily_values(d):
  icu_name_to_department = load_icu_name_to_department()
  dates = sorted(list(d.date.unique()))
  icu_names = sorted(list(d.icu_name.unique()))
  clean_data_points = list()
  per_icu_prev_data_point = dict()
  for date, icu_name in itertools.product(dates, icu_names):
    sd = d.loc[(d.date == date) & (d.icu_name == icu_name)]
    sd = sd.sort_values(by="datetime")
    new_data_point = {
      "date": date,
      "icu_name": icu_name,
      "department": icu_name_to_department[icu_name],
      "datetime": date,
    }
    new_data_point.update({col: 0 for col in CUM_COLUMNS})
    new_data_point.update({col: 0 for col in NCUM_COLUMNS})
    if icu_name in per_icu_prev_data_point:
      new_data_point.update({
        col: per_icu_prev_data_point[icu_name][col]
        for col in BEDCOUNT_COLUMNS
      })
    if len(sd) > 0:
      new_data_point.update({
        col: sd[col].iloc[-1]
        for col in BEDCOUNT_COLUMNS
      })
    per_icu_prev_data_point[icu_name] = new_data_point
    clean_data_points.append(new_data_point)
  return pd.DataFrame(clean_data_points)


def spread_cum_jumps(d, icu_to_first_input_date):
  assert np.all(d.date.values == d.datetime.values)
  date_begin_transfered_refused = pd.to_datetime("2020-03-25").date()
  dfs = []
  for icu_name, dg in d.groupby("icu_name"):
    dg = dg.sort_values(by="date")
    dg = dg.reset_index()
    already_fixed_col = set()
    for switch_point, cols in (
      (icu_to_first_input_date[icu_name], CUM_COLUMNS),
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
        beg_val = dg.loc[dg.date == beg, col].values[0]
        end_val = dg.loc[dg.date == end, col].values[0]
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


def load_data_file(data_path):
  ext = data_path.rsplit(".", 1)[-1]
  if ext == "pickle":
    with open(data_path, "rb") as f:
      d = pickle.load(f)
  elif ext == "h5":
    d = pd.read_hdf(data_path)
  elif ext == "csv":
    d = pd.read_csv(data_path)
  else:
    raise ValueError(f"unknown extension {ext}")
  return d


def load_icu_name_to_department():
  with open(DATA_PATHS["icu_name_to_department"]) as f:
    icu_name_to_department = json.load(f)
  icu_name_to_department["St-Dizier"] = "Haute-Marne"
  return icu_name_to_department


def load_department_population():
  return dict(
    pd.read_csv(DATA_PATHS["department_population"]
                ).itertuples(name=None, index=False)
  )


def load_france_departments():
  return pd.read_json(DATA_PATHS["departments"])


def load_public(cached_data=None):
  filename_prefix = "donnees-hospitalieres-covid19-2020"
  logging.info("scrapping public data")
  url = (
    "https://www.data.gouv.fr/fr/datasets/"
    "donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/"
  )
  with urllib.request.urlopen(url) as f:
    html_content = f.read().decode("utf8")
  tree = html.fromstring(html_content)
  download_url = None
  elements = tree.xpath('//*[contains(@class, "resource-card")]')
  for e in elements:
    resource_name = e.xpath('//*[contains(@class, "ellipsis")]/text()')[0]
    if resource_name.startswith(filename_prefix):
      download_url = e.xpath("//*[@download]/@href")[0]
      logging.info("found resource %s at %s" % (resource_name, download_url))
      break
  if download_url is None:
    raise Exception("Could not scrap public data")
  d = pd.read_csv(
    download_url,
    sep=";",
  )
  d = d.loc[d.sexe == 0]
  d = d.rename(
    columns={
      "dep": "department_code",
      "jour": "date",
      "hosp": "n_hospitalised_patients",
      "rea": "n_icu_patients",
    }
  )
  d["date"] = pd.to_datetime(d["date"]).dt.date
  return d[[
    "date",
    "department_code",
    "n_hospitalised_patients",
    "n_icu_patients",
  ]]


DEPARTMENTS = list(load_icu_name_to_department().values())
DEPARTMENTS_GRAND_EST = [
  "Ardennes", "Aube", "Marne", "Haute-Marne", "Meurthe-et-Moselle", "Meuse",
  "Moselle", "Bas-Rhin", "Haut-Rhin", "Vosges"
]
ICU_NAMES_GRAND_EST = list(
  k for k, v in load_icu_name_to_department().items()
  if v in set(DEPARTMENTS_GRAND_EST)
)
CODE_TO_DEPARTMENT = dict(
  load_france_departments()[["departmentCode", "departmentName"]].itertuples(
    name=None,
    index=False,
  ),
)
DEPARTMENT_TO_CODE = dict(
  load_france_departments()[["departmentName", "departmentCode"]].itertuples(
    name=None,
    index=False,
  )
)
DEPARTMENT_POPULATION = load_department_population()


def load_combined_bedcounts_public(api_key=None, cached_data=None, **kwargs):
  get_dpt_pop = load_department_population().get
  dp = load_if_not_cached("public", cached_data)
  dp["department"] = dp.department_code.apply(CODE_TO_DEPARTMENT.get)
  dp = dp.loc[dp.department.isin(DEPARTMENTS_GRAND_EST)]
  di = load_if_not_cached("bedcounts", cached_data)
  di = di.loc[di.icu_name.isin(ICU_NAMES_GRAND_EST)]
  di = di.groupby(["date", "department"]).sum().reset_index()
  di["department_code"] = di.department.apply(DEPARTMENT_TO_CODE.get)
  di["n_icu_patients"] = di.n_covid_occ + di.n_ncovid_occ.fillna(0)
  combined = di.merge(
    dp, on=["department", "date"], suffixes=["_icubam", "_public"]
  )
  combined["department_pop"] = combined.department.apply(get_dpt_pop)
  return combined
