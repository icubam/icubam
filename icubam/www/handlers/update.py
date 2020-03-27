import time

from absl import logging

from icubam.www.handlers import base
from icubam.www.handlers import home


def time_ago(ts) -> str:
  if ts is None:
    return 'jamais'

  delta = int(time.time() - int(ts))
  units = [(86400, 'jour'), (3600, 'heure'), (60, 'minute'), (1, 'seconde')]
  for unit, name in sorted(units, reverse=True):
    curr = delta // unit
    if curr > 0:
      plural = '' if curr == 1 else 's' # hack
      return 'il y a {} {}{}'.format(curr, name, plural)
  return 'à l\'instant'


class UpdateHandler(base.BaseHandler):

  ROUTE = '/update'
  QUERY_ARG = 'id'

  def initialize(self, config, db, queue, token_encoder):
    self.config = config
    self.db = db
    self.queue = queue
    self.token_encoder = token_encoder

  def get_icu_data_by_id(self, icu_id):
    df = self.db.get_bedcount_by_icu_id(icu_id)
    result = df.to_dict(orient="records")[0] if df is not None and not df.empty else None
    result['since_update'] = time_ago(result["update_ts"])
    result['home_route'] = home.HomeHandler.ROUTE
    result['update_route'] = self.ROUTE
    return result

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    input_data = self.token_encoder.decode(user_token)

    if input_data is None:
      return self.redirect('/error')

    try:
      data = self.get_icu_data_by_id(input_data['icu_id'])
      data.update(input_data)
      data.update(version=self.config.version)

      self.set_secure_cookie(self.COOKIE, user_token)
      self.render('update_form.html', **data)

    except Exception as e:
      logging.error(e)
      return self.redirect('/error')

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
