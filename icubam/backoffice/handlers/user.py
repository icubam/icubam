"""Creating/edition of users."""
import json
import tornado.escape
import tornado.web

from icubam.backoffice.handlers.base import BaseHandler
from icubam.backoffice.handlers.list_users import ListUsersHandler
from icubam.db.store import User


class UserHandler(BaseHandler):

  ROUTE = "/user"

  @tornado.web.authenticated
  def get(self):
    # TODO(fred): load the ICUs to show in the form.
    self.render("user.html", icus=[], user=User(), error="")

  def error(self, error_message, user):
    self.render("user.html", icus=[], user=user, error=error_message)

  @tornado.web.authenticated
  def post(self):
    # We first create a potential user object, because if the validation fails,
    # we send it back to the client and the client can re-fill the form with
    # the info that was sent.
    user = User(name=self.get_body_argument("name", ""),
      telephone=self.get_body_argument("telephone", ""),
      email=self.get_body_argument("email", ""),
      password_hash=self.store.get_password_hash(
        self.get_body_argument("password", "")))

    if not user.name:
      return self.error("Missing or invalid user name", user)

    if not user.email:
      return self.error("Missing or invalid user email", user)

    if not user.password_hash:
      return self.error("Missing or invalid password", user)

    if not user.telephone:
      return self.error("Missing or invalid telephone", user)

    try:
      # TODO(fred): we have to call add_user_to_icu as well.
      result = self.store.add_user(user)
    except Exception as e:
      return self.error("Error to create the user: {0}".format(e))

    return self.redirect(ListUsersHandler.ROUTE)
