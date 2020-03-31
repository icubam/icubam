import json
import tornado.escape
import tornado.web

from icubam.backoffice.handlers.base import BaseHandler


class ListUsersHandler(BaseHandler):

  ROUTE = "/list_users"

  # No need to send info such as the password of the user.
  def _cleanUser(self, user):
    user.password_hash = ""
    return user

  @tornado.web.authenticated
  def get(self):
    if self.get_current_user().is_admin:
      users = self.store.get_users()
    else:
      users = self.store.get_managed_users(self.user.user_id)

    output = [self._cleanUser(user) for user in users]
    self.render("list_users.html", users=output)
