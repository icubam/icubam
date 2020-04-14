"""Creating/edition of ICUs."""
from absl import logging
import json
import tornado.web

from icubam.backoffice.handlers import base


class ConsentResetHandler(base.BaseHandler):
  ROUTE = "reset_consent"

  def answer(self, msg, error=None):
    logging.error(f"{msg}: {error}")
    return self.write(json.dumps({'msg': msg, 'error': error}))

  @tornado.web.authenticated
  def post(self):
    try:
      user_id = json.loads(self.request.body.decode())
    except Exception as err:
      return self.answer(f'Cannot read request', error=f'{err}')

    try:
      self.db.update_user(
        self.current_user.user_id, user_id, dict(consent=None)
      )
    except Exception as err:
      return self.answer('Cannot reset consent', error=f'{err}')

    return self.answer('OK!')