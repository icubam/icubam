from absl import logging  # noqa: F401
from icubam import authenticator
from icubam import time_utils
from icubam.db import store
from icubam.www.handlers import home


def apply_default(data: dict, value: int, prefix: str):
  """Applies default values to undefined entries of a dict matching a prefix."""
  for k in data:
    if data[k] is None and k.startswith(prefix):
      data[k] = value


class Updater:
  """Helper class for dealing with updating the counts."""

  ROUTE = '/update'
  POST_ROUTE = '/update_counts'

  def __init__(self, config, db):
    self.config = config
    self.db = db
    self.authenticator = authenticator.Authenticator(self.config, self.db)

  def get_url(self, user_id: int, icu_id: int, update: bool = False) -> str:
    """Returns the url for the update form for the given user and icu.
    
    Args:
     user_id: the user id of the target user.
     icu_id: the icu id of the target icu.
     update: should we update the token in the db in case it is stale.
    """
    return "{}{}?id={}".format(
      self.config.server.base_url, self.ROUTE.strip('/'),
      self.authenticator.get_or_new_token(user_id, icu_id, update=update)
    )

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
