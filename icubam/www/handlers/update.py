from absl import logging  # noqa: F401
import tornado.web
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
    user, icu = self.decode_token(user_token)
    if user is None or icu is None:
      logging.error(f"Token authentication failed")
      self.clear_cookie(self.COOKIE)
      return self.set_status(404)

    locale = self.get_user_locale()
    data = self.updater.get_icu_data_by_id(icu.icu_id, locale=locale)
    data['icu_name'] = icu.name
    data['version'] = icubam.__version__
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

    try:
      params_str = self.request.body.decode()
      data = dict([parse(p) for p in params_str.split('&')])
    except Exception as e:
      logging.error(f'Error receiving update form: {e}')
      return

    data['user_id'] = self.user.user_id
    data['icu_id'] = self.icu.icu_id
    await self.queue.put(data)

    self.redirect(home.HomeHandler.ROUTE)
