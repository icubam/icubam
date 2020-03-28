import time

from absl import logging

from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam import time_utils


class UpdateHandler(base.BaseHandler):

  ROUTE = '/update'
  QUERY_ARG = 'id'

  def initialize(self, config, db, queue, token_encoder):
    super().initialize(config, db)
    self.queue = queue
    self.token_encoder = token_encoder

  def get_icu_data_by_id(self, icu_id, def_val=0):
    df = self.db.get_bedcount()
    try:
      data = None
      last_update = None
      for index, row in df[df.icu_id == icu_id].iterrows():
        data = row.to_dict()
        last_update = data['update_ts']
        break
    except Exception as e:
      logging.error(e)
      data = {x: def_val for x in df.columns.to_list() if x.startswith('n_')}
    if data is None:
      data = {x: def_val for x in df.columns.to_list() if x.startswith('n_')}
    for k in data:
      if data[k] is None:
        data[k] = def_val

    data['since_update'] = time_utils.localwise_time_ago(
      last_update, self.get_user_locale())
    data['home_route'] = home.HomeHandler.ROUTE
    data['update_route'] = self.ROUTE
    return data

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    input_data = self.token_encoder.decode(user_token)

    if input_data is None:
      return self.set_status(404)

    try:
      data = self.get_icu_data_by_id(input_data['icu_id'])
      data.update(input_data)
      data.update(version=self.config.version)

      self.set_secure_cookie(self.COOKIE, user_token)
      self.render('update_form.html', **data)

    except Exception as e:
      logging.error(e)
      return self.set_status(404)

  async def post(self):
    """Reads the form and saves the data to DB"""

    def parse(param):
      parts = param.split('=')
      value = int(parts[1]) if parts[1].isnumeric() else 0
      return parts[0], value

    cookie_data = self.token_encoder.decode(self.get_secure_cookie(self.COOKIE))

    params_str = self.request.body.decode()
    data = dict([parse(p) for p in params_str.split('&')])
    data.update(cookie_data)
    await self.queue.put(data)

    self.redirect(home.HomeHandler.ROUTE)
