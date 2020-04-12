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

  def authenticate_from_token(self, user_token):
    input_data = self.token_encoder.decode(user_token)
    if input_data is None:
      logging.error("No token to be found.")
      return None, None

    userid = int(input_data.get('user_id', -1))
    user = self.db.get_user(userid)
    if user is None:
      logging.error(f"User does not exist.")
      return None, None

    icuid = int(input_data.get('icu_id', -1))
    user_icu_ids = [i.icu_id for i in user.icus]
    if icuid not in user_icu_ids:
      logging.error(f"User does not belong the ICU.")
      return None, None

    if user.consent is not None and not user.consent:
      logging.error(f"User has bailed out from ICUBAM.")
      return None, None

    return user, input_data

  async def get(self):
    """Serves the page with a form to be filled by the user."""
    user_token = self.get_query_argument(self.QUERY_ARG)
    user, token_data = self.authenticate_from_token(user_token)
    if user is None:
      logging.error(f"Token authentication failed")
      return self.set_status(404)

    locale = self.get_user_locale()
    icu_id = int(token_data.get('icu_id', -1))
    data = self.updater.get_icu_data_by_id(icu_id, locale=locale)
    data.update(token_data)
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
