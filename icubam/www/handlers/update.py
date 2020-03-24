from absl import logging
import json
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token


class UpdateHandler(base.BaseHandler):

  ROUTE = '/update'
  QUERY_ARG = 'id'

  def initialize(self, db, queue):
    self.db = db
    self.queue = queue

  def get_icu_data(self, icu_id, def_val=10):
    df = self.db.get_bedcount()
    try:
      data = None
      for index, row in df[df.icu_id == icu_id].iterrows():
        data = row.to_dict()
        break
    except Exception as e:
      logging.error(e)
      data = {x: def_val for x in df.columns.to_list() if x.startswith('n_')}

    if data is None:
      data = {x: def_val for x in df.columns.to_list() if x.startswith('n_')}

    for k in data:
      if data[k] is None:
        data[k] = def_val

    return data

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    input_data = token.decode(user_token)

    if input_data is None:
      return self.redirect('/error')

    data = self.get_icu_data(input_data['icu_id'])
    data.update(input_data)
    print('--> ', data)
    self.set_secure_cookie(self.COOKIE, user_token)
    self.render('update_form.html', **data)

  async def post(self):
    def parse(param):
      parts = param.split('=')
      return parts[0], int(parts[1])

    data = dict([parse(p) for p in self.request.body.decode().split('&')])
    data.update(token.decode(self.get_secure_cookie(self.COOKIE)))
    await self.queue.put(data)
    self.redirect(home.HomeHandler.ROUTE)
