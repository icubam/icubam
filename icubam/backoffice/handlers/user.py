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
    self.render("user.html", icus=[])

  def error(self, error_message):
    return self.redirect(self.ROUTE + "?error={}".format(error_message))

  @tornado.web.authenticated
  def post(self):
    input = {}
    for argument in ["name", "email", "password", "country_code", "phone"]:
      value = self.get_body_argument(argument, "")
      if not value:
        return self.error("Missing info {}".format(argument))
      input[argument] = value

    country_code = input.get("country_code")
    phone = "+{}{}".format(country_code.replace('+', ''), input.get("phone"))

    user = User(name=input.get("name"),
      telephone=phone,
      email=input.get("email"),
      password_hash=self.store.get_password_hash(input.get("password")))

    try:
      # TODO(fred): we have to call add_user_to_icu as well.
      result = self.store.add_user(user)
    except Exception as e:
      return self.error("Error to create the user: {0}".format(e))

    return self.redirect(ListUsersHandler.ROUTE)
