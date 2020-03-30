import json
import tornado.escape

from icubam.backoffice.handlers.store import StoreHandler


class ListUsersHandler(StoreHandler):

  ROUTE = "/list_users"

  # No need to send info such as the password of the user.
  def _cleanUser(self, user):
    user.password_hash = ""
    return user

  def getForUser(self, user):
    managed_users = self.store.get_managed_users(user.user_id)
    output = []
    for managed in managed_users:
        output.append(self._cleanUser(managed))

    self.render("list_users.html", users=output)
