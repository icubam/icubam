from absl import logging  # noqa: F401
from icubam import time_utils
from icubam.db import store
from icubam.www.handlers import home
from icubam.www import token


def apply_default(data: dict, value: int, prefix: str):
  """Applies default values to undefined entries of a dict matching a prefix."""
  for k in data:
    if data[k] is None and k.startswith(prefix):
      data[k] = value


class Updater:
  """Helper class for dealing with updating the counts."""

  GET_ROUTE = '/update_form'
  POST_ROUTE = '/update'

  def __init__(self, config, db):
    self.config = config
    self.db = db
    self.token_encoder = token.TokenEncoder(self.config)

  def get_user_url(self, user, icu_id: str) -> str:
    icu = {i.icu_id: i for i in user.icus}.get(icu_id, None)
    if icu is not None:
      return self.get_url(user, icu)

  def get_url(self, user, icu) -> str:
    return "{}{}?id={}".format(
      self.config.server.base_url, self.ROUTE.strip('/'),
      self.token_encoder.encode_data(user, icu)
    )

  def get_urls(self):
    result = []
    for user in self.db.get_users():
      for icu in user.icus:
        result.append(self.get_url(icu.icu_id, icu.name))
    return result

  def get_icu_data_by_id(self, icu_id, locale=None, def_val=0):
    """Returns the dictionary of counts for the given icu."""
    bed_count = self.db.get_bed_count_for_icu(icu_id)
    bed_count = bed_count if bed_count is not None else store.BedCount()
    # In case there is a weird corner case, we don't want to crash the form:
    last_update = bed_count.last_modified
    if last_update is not None:
      last_update = last_update.timestamp()
    result = bed_count.to_dict()
    apply_default(result, value=def_val, prefix='n_')
    result['since_update'] = time_utils.localewise_time_ago(
      last_update, locale
    )
    result['home_route'] = home.HomeHandler.ROUTE
    result['update_route'] = self.POST_ROUTE
    return result
