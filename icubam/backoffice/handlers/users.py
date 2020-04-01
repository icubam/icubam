"""Creating/edition of users."""
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import store


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
    columns = [] if not data else list(data[0].keys())
    self.render(
      "list.html", data=data, columns=columns, objtype='Users',
      create_route=UserHandler.ROUTE)


class ProfileHandler(base.BaseHandler):
  ROUTE = "/profile"

  @tornado.web.authenticated
  def get(self):
    return self.redirect(
      '{}?id={}'.format(UserHandler.ROUTE, self.user.user_id))



class UserHandler(base.BaseHandler):
  ROUTE = "/user"

  @tornado.web.authenticated
  def get(self):
    userid = self.get_query_argument('id', None)
    user = None
    if userid is not None:
      user = self.db.get_user(userid)
    # TODO(fred): load the ICUs to show in the form.
    user = user if user is not None else store.User()
    self.render("user.html", icus=[], user=user, error="")

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
