import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import user


class ListUsersHandler(base.BaseHandler):

  ROUTE = "/list_users"

  # No need to send info such as the password of the user.
  def _cleanUser(self, user):
    user_dict = user.to_dict()
    user_dict.pop("password_hash", None)
    user_dict.pop("access_salt", None)
    return user_dict

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      users = self.store.get_users()
    else:
      users = self.store.get_managed_users(self.user.user_id)

    data = [self._cleanUser(user) for user in users]
    colums = [] if not data else list(data[0].keys())
    self.render(
      "list.html", data=data, columns=columns, objtype='Users',
      create_route=user.UserHandler.ROUTE)
