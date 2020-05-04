import datetime
import functools
import inspect
import time
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
  "icu_name", "date", "datetime", "department", "region_id", "region",
  "create_date"
] + CUM_COLUMNS + NCUM_COLUMNS)


def cached(func):
  """A cached decorator for a method. The class must have a ttl parameter."""
  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    # Build a cache key for this call, taking default values into account.
    argspec = inspect.getfullargspec(func)
    key_dict = {
      argspec.args[-i]: argspec.defaults[-i]
      for i in range(1,
                     len(argspec.defaults) + 1)
    }
    if argspec.kwonlydefaults is not None:
      key_dict.update(argspec.kwonlydefaults)
    func_args = argspec.args[1:]
    key_dict.update({k: v for k, v in zip(func_args, args)})
    key_dict.update(kwargs)
    key = tuple(sorted(key_dict.items()))

    if getattr(self, 'cache', None) is None:
      setattr(self, 'cache', {})

    value = self.cache.get(key, None)
    if value is not None and time.time() - value[1] <= self.ttl:
      return value[0]

    self.cache.pop(key, None)
    result = func(self, *args, **kwargs)
    self.cache[key] = (result, time.time())
    return result

  return wrapper


class Dataset:
  """A class to manipulate the bedcounts data. With caching support."""
  COLLECTIONS = ['icus', 'regions', 'bedcounts', 'all_bedcounts']

  def __init__(self, db, ttl: int = 0):
    self.db = db
    self.ttl = ttl

  @cached
  def get_bedcounts(self, max_ts=None, latest=False, preprocess=True):
    if isinstance(max_ts, str) and max_ts.isnumeric():
      max_ts = datetime.datetime.fromtimestamp(int(max_ts))

    result = None
    if latest:
      result = self.db.get_visible_bed_counts_for_user(
        user_id=None, force=True, max_date=max_ts
      )
    else:
      result = self.db.get_bed_counts(max_date=max_ts)

    result = store.to_pandas(result, max_depth=2)
    result = result.drop(
      columns=['icu_bed_counts', 'icu_users', 'icu_managers']
    )
    if preprocess:
      result = preprocessing.preprocess_bedcounts(result)

    result = result.sort_values(by=["create_date", "icu_name"])
    return result

  def get(self, collection='bedcounts', max_ts=None):
    """Returns the proper pandas dataframe."""
    if collection in ['bedcounts', 'all_bedcounts']:
      latest = collection == 'bedcounts'
      return self.get_bedcounts(max_ts, latest=latest, preprocess=not latest)

    if collection == 'icus':
      result = self.db.get_icus()
    else:
      result = self.db.get_regions()
    return store.to_pandas(result, max_depth=0)
