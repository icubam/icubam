import inspect
import json
import logging
import pickle
import urllib.request
from pathlib import Path
from typing import Optional

import pandas as pd
from lxml import html

BASE_PATH = Path(__file__).resolve().parent

DATA_SOURCES = {"icubam", "bedcounts", "public", "combined_bedcounts_public"}

DATA_PATHS = {
  "department_population": "data/department_population.csv",
  "departments": "data/france_departments.json",
  "department_typo_fixes": "data/icubam_department_typo_fixes.json",
}

for key, path in DATA_PATHS.items():
  DATA_PATHS[key] = str(Path(BASE_PATH) / path)


def load_department_population():
  return dict(
    pd.read_csv(DATA_PATHS["department_population"]
                ).itertuples(name=None, index=False)
  )


def load_france_departments():
  return pd.read_json(DATA_PATHS["departments"])


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
DEPARTMENTS = set(load_france_departments().departmentName.unique())

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
ALL_COLUMNS = (["icu_name", "date", "datetime", "department", "region"] +
               CUM_COLUMNS + NCUM_COLUMNS)


def load_if_not_cached(data_source, cached_data, **kwargs):
  """Load a single data source if it is not in cached data"""
  if data_source not in DATA_SOURCES:
    raise ValueError(f"Unknown data source: {data_source}")
  load_data_fun = globals().get(f"load_{data_source}", None)
  if load_data_fun is None:
    raise RuntimeError(
      f"No loading function associated to data source {data_source}"
    )
  if cached_data is None or data_source not in cached_data:
    load_data_fun_signature = inspect.signature(load_data_fun)
    kwargs = {
      k: v
      for k, v in kwargs.items()
      if k in load_data_fun_signature.parameters
    }
    if 'cached_data' in load_data_fun_signature.parameters:
      kwargs['cached_data'] = cached_data
    return load_data_fun(**kwargs)
  return cached_data[data_source]


def load_bedcounts(
  preprocess=True,
  spread_cum_jump_correction=False,
  api_key=None,
  icubam_host=None,
  max_date=None,
  cached_data=None,
  restrict_to_region: Optional[str] = None,
):
  """Load Bedcount data from ICUBAM API"""
  d = load_if_not_cached(
    "icubam",
    cached_data,
    api_key=api_key,
    icubam_host=icubam_host,
    restrict_to_region=restrict_to_region,
  )
  if preprocess:
    from icubam.predicu.preprocessing import preprocess_bedcounts
    d = preprocess_bedcounts(d, spread_cum_jump_correction)
  d = d.sort_values(by=["date", "icu_name"])
  if max_date is not None:
    logging.info("data loaded's max date will be %s (excluded)" % max_date)
    d = d.loc[d.date < pd.to_datetime(max_date).date()]
  return d


def load_icubam(
  cached_data=None,
  api_key=None,
  icubam_host=None,
  preprocess=True,
  restrict_to_region: Optional[str] = None,
):
  if cached_data is not None and "raw_icubam" in cached_data:
    d = cached_data["raw_icubam"]
  else:
    if api_key is None or icubam_host is None:
      raise RuntimeError("Provide API key and host to download ICUBAM data")
    else:
      protocol = ("http" if icubam_host.startswith("localhost") else "https")
      url = (
        f"{protocol}://{icubam_host}/"
        f"db/all_bedcounts?format=csv&API_KEY={api_key}"
      )
      logging.info("downloading data from %s" % url)
      d = pd.read_csv(url.format(api_key))
  if preprocess:
    if restrict_to_region is not None:
      if restrict_to_region == 'Grand-Est':
        region_id = 1
        d = d.loc[d.icu_region_id == region_id]
      else:
        raise NotImplementedError
    d = d.rename(columns={"create_date": "date", "icu_dept": "department"})
    d.loc[d.icu_name == "St-Dizier", "department"] = "Haute-Marne"
    with open(DATA_PATHS["department_typo_fixes"]) as f:
      department_typo_fixes = json.load(f)
    for wrong_name, right_name in department_typo_fixes.items():
      d.loc[d.department == wrong_name, "department"] = right_name
    d["region"] = d.icu_region_id
    d = format_data(d)
  return d


def load_pre_icubam(data_path):
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
  d = format_data(d)
  return d


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


def load_public():
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
      "rad": "n_hospital_healed",
      "dc": "n_hospital_death",
    }
  )
  d["date"] = pd.to_datetime(d["date"]).dt.date
  return d[[
    "date",
    "department_code",
    "n_hospitalised_patients",
    "n_icu_patients",
    "n_hospital_healed",
    "n_hospital_death",
  ]]


def load_combined_bedcounts_public(
  api_key=None,
  cached_data=None,
  icubam_host=None,
  restrict_to_region: Optional[str] = None,
):
  get_dpt_pop = load_department_population().get
  dp = load_if_not_cached("public", cached_data)
  dp["department"] = dp.department_code.apply(CODE_TO_DEPARTMENT.get)
  di = load_if_not_cached(
    "bedcounts", cached_data, api_key=api_key, icubam_host=icubam_host
  )
  dpt_to_region = dict(
    di.groupby(["department", "region"]
               ).first().reset_index()[["department", "region"
                                        ]].itertuples(name=None, index=False)
  )
  di = di.groupby(["date", "department"]).sum().reset_index()
  di["department_code"] = di.department.apply(DEPARTMENT_TO_CODE.get)
  di["n_icu_patients"] = di.n_covid_occ + di.n_ncovid_occ.fillna(0)
  d = di.merge(dp, on=["department", "date"], suffixes=["_icubam", "_public"])
  d["department_pop"] = d.department.apply(get_dpt_pop)
  d["region"] = d.department.apply(dpt_to_region.get)
  if restrict_to_region is not None:
    if restrict_to_region == 'Grand-Est':
      region_id = 1
      d = d.loc[d.region == region_id]
    else:
      raise NotImplementedError
  return d


def format_data(d):
  d["datetime"] = pd.to_datetime(d["date"])
  d["date"] = d["datetime"].dt.date
  d = d[ALL_COLUMNS]
  return d
