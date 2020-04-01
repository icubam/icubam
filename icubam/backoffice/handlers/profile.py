"""Creating/edition of users."""
import json
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import user
from icubam.backoffice.handlers import list_users
from icubam.db.store import User


class ProfileHandler(base.BaseHandler):

  ROUTE = "/profile"

  @tornado.web.authenticated
  def get(self):
    return self.redirect(
      '{}?id={}'.format(user.UserHandler.ROUTE, self.user.user_id))
