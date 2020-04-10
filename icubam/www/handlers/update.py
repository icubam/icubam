from absl import logging  # noqa: F401
import os.path

import icubam
from icubam.www.handlers import base
from icubam.www.handlers import home
from icubam.www import updater


class UpdateHandler(base.BaseHandler):

  ROUTE = updater.Updater.ROUTE
  QUERY_ARG = 'id'

  def initialize(self, config, db_factory, queue):
    super().initialize(config, db_factory)
    self.queue = queue
    self.updater = updater.Updater(self.config, self.db)

  def get_consent_html(self, user):
    """To show a consent modal, the user should be seeing it for the first time
    and we should have an agreement form to show."""
    path = self.config.server.consent
    # The user has already agreed, we skip.
    if not user.consent and path is not None and os.path.exists(path):
      with open(path, 'r') as fp:
        return fp.read()

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    input_data = self.token_encoder.decode(user_token)

    if input_data is None:
      return self.set_status(404)

    userid = int(input_data.get('user_id', -1))
    user = self.db.get_user(userid)
    if user is None:
      logging.error(f"No such user {userid}")
      return self.set_status(404)

    data = self.updater.get_icu_data_by_id(
      input_data['icu_id'], locale=self.get_user_locale()
    )
    data.update(input_data)
    data.update(version=icubam.__version__)

    # Show consent form?
    data['consent'] = self.get_consent_html(user)

    self.set_secure_cookie(self.COOKIE, user_token)
    self.render('update_form.html', **data)

  @tornado.web.authenticated
  async def post(self):
    """Reads the form and saves the data to DB"""
    def parse(param):
      parts = param.split('=')
      value = int(parts[1]) if parts[1].isnumeric() else 0
      return parts[0], value

    cookie_data = self.token_encoder.decode(
      self.get_secure_cookie(self.COOKIE)
    )

    params_str = self.request.body.decode()
    data = dict([parse(p) for p in params_str.split('&')])
    data.update(cookie_data)
    await self.queue.put(data)

    self.redirect(home.HomeHandler.ROUTE)
