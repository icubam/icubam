import logging
import pickle
import urllib.request
from pathlib import Path
from typing import Callable, Dict

import pandas as pd
from lxml import html

BASE_PATH = Path(__file__).resolve().parent

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
  d = pd.read_json(DATA_PATHS["departments"])
  d.loc[d["departmentName"] == "Côtes-d'armor",
        "departmentName"] = "Côtes-d'Armor"
  return d


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


def load_data(data_source: str, **kwargs):
  """Generic data loader for various data sources

    Args:
      data_source: must be one of DATA_SOURCES
    """
  if data_source == 'combined_bedcounts_public':
    raise ValueError(
      'combined_bedcounts_public must be manually assembled '
      'from bedcounts and public data sources'
    )
  elif data_source not in DATA_LOADERS:
    raise ValueError(f'data_source={data_source} not in {DATA_SOURCES}.')

  func = DATA_LOADERS[data_source]
  # If kwargs are wrong, this will explicitly fail. It's up to the user to pass
  # correct arguments for each data loader.
  return func(**kwargs)


def load_bedcounts(
  api_key=None,
  icubam_host=None,
):
  """Load Bedcount data from ICUBAM API"""
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
  d = d.sort_values(by=["create_date", "icu_name"])
  return d


def load_pre_icubam(data_path):
  d = _load_any_file(data_path)
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


def _load_any_file(data_path):
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


def combine_bedcounts_public(
  public_data: pd.DataFrame, bedcount_data: pd.DataFrame
) -> pd.DataFrame:
  """Combine **preprocessed** public and ICUBAM data"""
  get_dpt_pop = load_department_population().get
  dp = public_data
  di = bedcount_data
  dp["department"] = dp.department_code.apply(CODE_TO_DEPARTMENT.get)
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
  return d


def format_data(d):
  d["datetime"] = pd.to_datetime(d["date"])
  d["date"] = d["datetime"].dt.date
  d = d[ALL_COLUMNS]
  return d


DATA_LOADERS: Dict[str, Callable] = {
  "bedcounts": load_bedcounts,
  "public": load_public
}
# note that there is no loader for combined_bedcounts_public, it must be
# explicitly assembled with `combine_bedcounts_public` function after
# pre-processing
DATA_SOURCES = ["bedcounts", "public", "combined_bedcounts_public"]
