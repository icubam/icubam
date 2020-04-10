from absl import logging
import json
import tornado.web

from icubam.www.handlers import base


class ConsentHandler(base.BaseHandler):

  ROUTE = '/consent'
  ARGUMENT = 'agree'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    admins = self.db.get_admins()
    self.admin_id = admins[0].user_id if admins else self.db.add_default_admin()

  @tornado.web.authenticated
  def post(self):
    """Depending on which button the user has clicked, we decide to set the
    consent field of the user to True or False.

    If False, the user has no access to ICUBAM and it is considered as
    inactive. Otherwise we won't ask again and acces is granted.
    """
    agree = bool(int(self.get_body_argument(self.ARGUMENT, '0')))
    result = {}
    if agree:
      logging.info(f'user {self.user.user_id} consents.')
      self.db.update_user(
        self.admin_id, self.user.user_id, dict(consent=True, is_active=True))
      result['redirect'] = None
    else:
      logging.info(f'user {self.user.user_id} does not consent.')
      self.db.update_user(
        self.admin_id, self.user.user_id, dict(consent=False, is_active=False))
      result['redirect'] = self.ROUTE
      self.clear_cookie(self.COOKIE)
    return self.write(json.dumps(result))

  def get(self):
    self.write("You do not have access to ICUBAM services.")
