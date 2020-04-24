from pathlib import Path

from absl import logging  # noqa: F401

from icubam.analytics import preprocessing
from icubam.db import store

BASE_PATH = Path(__file__).resolve().parent

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
ALL_COLUMNS = ([
  "icu_name", "icu_region_name", "date", "datetime", "department", "region"
] + CUM_COLUMNS + NCUM_COLUMNS)


def load_bedcounts(db, preprocess: bool = False):
  """Load Bedcount data from ICUBAM DB"""
  bc = store.to_pandas(db.get_bed_counts(), max_depth=2)
  bc = preprocessing.preprocess_bedcounts(bc)
  bc = bc.sort_values(by=["create_date", "icu_name"])
  return bc
