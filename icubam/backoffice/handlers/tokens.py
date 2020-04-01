import tornado.escape
import tornado.web

from icubam.backoffice.handlers.base import BaseHandler


class ListUsersHandler(BaseHandler):

  ROUTE = "/list_tokens"

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      users = self.store.get_users()
    else:
      users = self.store.get_managed_users(self.user.user_id)

    output = [self._cleanUser(user) for user in users]
    self.render("list_users.html", users=output)
