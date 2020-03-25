from absl import logging
import json
import time
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token


def time_ago(ts) -> str:
  if ts is None:
    return 'Jamais'

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

  def initialize(self, db, queue, token_encoder):
    self.db = db
    self.queue = queue
    self.token_encoder = token_encoder

  def get_icu_data(self, icu_id, def_val=0):
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

    data['since_update'] = time_ago(last_update)
    return data

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    input_data = self.token_encoder.decode(user_token)

    if input_data is None:
      return self.redirect('/error')

    data = self.get_icu_data(input_data['icu_id'])
    data.update(input_data)

    self.set_secure_cookie(self.COOKIE, user_token)
    self.render('update_form.html', **data)

  async def post(self):
    def parse(param):
      parts = param.split('=')
      value = int(parts[1]) if parts[1].isnumeric() else 0
      return parts[0], value

    data = dict([parse(p) for p in self.request.body.decode().split('&')])
    data.update(self.token_encoder.decode(self.get_secure_cookie(self.COOKIE)))
    await self.queue.put(data)
    self.redirect(home.HomeHandler.ROUTE)
