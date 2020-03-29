import json
import tornado.escape

from icubam.backoffice.handlers.store import StoreHandler


class ListUsersHandler(StoreHandler):

  ROUTE = "/list_users"

  # No need to send info such as the password of the user.
  def _cleanUser(self, user):
    user.password_hash = ""

  def get(self, user):
    managed_users = self.db.get_managed_users(user.userid)
    output = []
    for managed in managed_users:
        output.append(self._cleanUser(managed))

    self.render("list_users.html", users=json.dumps(output))
