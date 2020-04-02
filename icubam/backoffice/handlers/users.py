"""Creating/edition of users."""
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.db import store
from icubam.db.store import User


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
      users = self.db.get_users()
    else:
      users = self.db.get_managed_users(self.user.user_id)

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

  """Creates ICU DTOs based on ALL ICUs and those from the selected."""
  def select_icus(self, selected_icus_ids):
    # TODO(olivier): restrict managers to regional icus
    icus = self.db.get_icus()
    output = []
    for icu in icus:
      dto = icu.to_dict()
      dto["selected"] = icu.icu_id in selected_icus_ids
      output.append(dto)
    return sorted(output, key = lambda x: x['name'])

  """Selects the DTO comparing ALL icus against the ones from the user."""
  def select_icus_for_user(self, user):
    return self.select_icus([user_icu.icu_id for user_icu in user.icus])

  @tornado.web.authenticated
  def get(self):
    userid = self.get_query_argument('id', None)
    user = None
    if userid is not None:
      user = self.db.get_user(userid)

    user = user if user is not None else store.User()
    icus_dto = self.select_icus_for_user(user)
    self.render("user.html", icus=icus_dto, user=user, error=False)

  def error(self, user, icus):
    self.render("user.html", icus=icus, user=user, error=True)

  """Returns the ICUs we need to add to/remove from the user. """
  def get_icus_to_store(self, user):
    form_icus = self.get_body_arguments("icus", [])
    form_icus = set([int(icu) for icu in form_icus])
    user_icus = set([user_icu.icu_id for user_icu in user.icus])
    add =  list(form_icus.difference(user_icus))
    remove = list(user_icus.difference(form_icus))
    return add, remove

  """Selects the DTO comparing ALL icus against the ones from the form."""
  def select_icus_for_error(self):
    form_icus = self.get_body_arguments("icus", [])
    return self.select_icus([int(icu) for icu in form_icus])

  @tornado.web.authenticated
  def post(self):
    user_dict = {}
    for key in ["name", "email", "telephone"]:
      user_dict[key] = self.get_body_argument(key, None)

    # Password is not required when editing the user.
    password = self.get_body_argument("password", None)
    if password:
      user_dict["password_hash"] = self.db.get_password_hash(password)

    uid = self.get_body_argument("user_id", None)
    if uid:
      user_dict["user_id"] = int(uid)

    # The admin info: we only show the ability to tag one user as admin in the
    # FE if the person logged in is also an admin. We don't override the bit
    # in the case the user is being changed by another person.
    if self.user.is_admin:
      user_dict['is_admin'] = self.get_body_argument("is_admin", None) == "on"

    # We want to keep this "temp" user, because if saving fails, we need to
    # dump this object back to the form, otherwise the person using the BO will
    # lose the changes that were done.
    # Important that this user HAS the id (in case this is an EDIT), otherwise
    # we will try to create a new user upon "Save" :)
    tmp_user = User(**user_dict)

    # Validates all the fields that must be validated.
    for value in user_dict.values():
      if value is None:
        return self.error(user=tmp_user, icus=self.select_icus_for_error())

    # Yet another validation step: checks password.
    # This should not be needed because the FE has validation patterns, but
    # let's be on the safe side.
    # note: not uid => this is a new user.
    if not uid and not password:
        return self.error(user=tmp_user, icus=self.select_icus_for_error())

    # To match the user ICUs from what we got from the form.
    user = tmp_user if not uid else self.db.get_user(int(uid))
    add, remove = self.get_icus_to_store(user)
    try:
      if not uid:
        uid = self.db.add_user(user)
      else:
        self.db.update_user(self.user.user_id, uid, user_dict)

      for icu in add:
        self.db.assign_user_to_icu(self.user.user_id, uid, icu)

      for icu in remove:
        self.db.remove_user_from_icu(self.user.user_id, uid, icu)

    except Exception as e:
      return self.error(user=tmp_user, icus=self.select_icus_for_error())

    return self.redirect(ListUsersHandler.ROUTE)
