from  absl import logging

from icubam import time_utils
from icubam.www.handlers import home
from icubam.www import token


class Updater:
  """Helper class for dealing with updating the counts."""

  ROUTE = '/update'

  def __init__(self, config, db):
    self.config = config
    self.db = db
    self.token_encoder = token.TokenEncoder(self.config)

  def get_url(self, icu_id: str, icu_name: str) -> str:
    return "{}{}?id={}".format(
      self.config.server.base_url,
      self.ROUTE.strip('/'),
      self.token_encoder.encode_icu(icu_id, icu_name))

  def get_urls(self):
    result = []
    for index, row in self.db.get_users().iterrows():
      result.append(self.get_url(row.icu_id, row.icu_name))
    return result

  def get_icu_data_by_id(self, icu_id, locale=None, def_val=0):
    """Returns the dictionary of counts for the given icu."""
    df = self.db.get_bedcount(icu_ids=[icu_id,])
    data = None
    last_update = None
    # In case there is a weird corner case, we don't want to crash the form:
    try:
      data = df.to_dict(orient='records')[0]
      last_update = data['update_ts']
    except Exception as e:
      logging.error(e)
      data = {x: def_val for x in df.columns.to_list() if x.startswith('n_')}
    if data is None:
      data = {x: def_val for x in df.columns.to_list() if x.startswith('n_')}
    for k in data:
      if data[k] is None:
        data[k] = def_val

    data['since_update'] = time_utils.localewise_time_ago(last_update, locale)
    data['home_route'] = home.HomeHandler.ROUTE
    data['update_route'] = self.ROUTE
    return data
