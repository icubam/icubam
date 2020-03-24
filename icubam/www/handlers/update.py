import json
import tornado.web
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token


class UpdateHandler(base.BaseHandler):

  ROUTE = '/update'
  QUERY_ARG = 'id'

  def initialize(self, queue):
    self.queue = queue

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    data = token.decode(user_token)
    if data is None:
      return self.redirect('/error')

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
