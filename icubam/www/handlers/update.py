from absl import logging  # noqa: F401
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import token
from icubam.www import updater


class UpdateHandler(base.BaseHandler):

  ROUTE = updater.Updater.ROUTE
  QUERY_ARG = 'id'

  def initialize(self, config, db, queue):
    super().initialize(config, db)
    self.queue = queue
    self.updater = updater.Updater(self.config, self.db)
    self.token_encoder = token.TokenEncoder(self.config)

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    input_data = self.token_encoder.decode(user_token)

    if input_data is None:
      return self.set_status(404)

    data = self.updater.get_icu_data_by_id(
      input_data['icu_id'], locale=self.get_user_locale())
    data.update(input_data)
    data.update(version=self.config.version)

    self.set_secure_cookie(self.COOKIE, user_token)
    self.render('update_form.html', **data)

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
