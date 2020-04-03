"""Creating/edition of users."""
from absl import logging

import tornado.escape
import tornado.web
from typing import List, Optional, Dict

from icubam.messaging import client
from icubam.backoffice.handlers import base
from icubam.db import store
from icubam.db.store import User


class ListUsersHandler(base.BaseHandler):
  ROUTE = "/list_users"

  # No need to send info such as the password of the user.
  def _cleanUser(self, user):
    user_dict = user.to_dict(include_relationships=False)
    user_dict.pop("password_hash", None)
    user_dict.pop("access_salt", None)
    return self.format_list_item(user_dict)

  @tornado.web.authenticated
  def get(self):
    if self.user.is_admin:
      users = self.db.get_users()
    else:
      users = self.db.get_managed_users(self.user.user_id)

    data = [self._cleanUser(user) for user in users]
    self.render(
      "list.html", data=data, objtype='Users', create_route=UserHandler.ROUTE)


class ProfileHandler(base.BaseHandler):
  ROUTE = "/profile"

  @tornado.web.authenticated
  def get(self):
    return self.redirect(
      '{}?id={}'.format(UserHandler.ROUTE, self.user.user_id))


class UserHandler(base.BaseHandler):
  ROUTE = "/user"

  def initialize(self, config, db):
    super().initialize(config, db)
    self.message_client = client.MessageServerClient(self.config)

  @tornado.web.authenticated
  def get(self):
    user = self.db.get_user(self.get_query_argument('id', None))
    user_icus = set([i.icu_id for i in user.icus]) if user is not None else []
    user_micus = set(
        [i.icu_id for i in user.managed_icus]) if user is not None else []
    return self.do_render(user, user_icus, user_micus, error=False)

  def do_render(self,
                user: store.User,
                icus: List[int],
                managed_icus: List[int],
                error=False):
    """Render the form for a given user."""

    user = user if user is not None else store.User()
    self.prepare_for_display(user)
    options = sorted(self.get_options(), key=lambda icu: icu.name)

    return self.render("user.html", options=options, user=user, icus=icus,
                       managed_icus=managed_icus, error=error)

  def get_options(self):
    if self.user.is_admin:
      options = self.db.get_icus()
    else:
      options = self.user.managed_icus
    return options

  def prepare_for_display(self, user: store.User):
    if user.is_active is None:
      user.is_active = True
    if user.is_admin is None:
      user.is_admin = False

  def prepare_for_save(self, user_dict: Dict, password: Optional[str]):
    """Cleaning input user_dict."""
    id_key = "user_id"
    # If the user is not set, the user_id comes empty and we need to remove it
    # before add to the db.
    if user_dict.get(id_key, "") == "":
      user_dict.pop(id_key, None)

    user_dict["is_active"] = user_dict.get("is_active", 'True') == 'True'
    user_dict["is_admin"] = user_dict.get("is_admin", 'False') == 'True'
    if password:
      user_dict["password_hash"] = self.db.get_password_hash(password)

    is_manager = len(user_dict.get('managed_icus', [])) > 0
    is_admin = user_dict.get('is_admin', False)
    if not is_admin and not is_manager:
      for key in ["password_hash", "email", "managed_icus"]:
        user_dict.pop(key, None)

    icus = set(map(int, user_dict.pop('icus', [])))
    managed_icus = set(map(int, user_dict.pop('managed_icus', [])))
    return icus, managed_icus

  @tornado.web.authenticated
  async def post(self):
    password = self.get_body_argument("password", None)
    user_dict = self.parse_from_body(store.User)
    icus, managed_icus = self.prepare_for_save(user_dict, password)
    try:
      await self.save_user(user_dict, icus, managed_icus)
    except Exception as e:
      user = store.User(**user_dict)
      return self.do_render(
        user=user, icus=icus, managed_icus=managed_icus, error=f'{e}')
    return self.redirect(ListUsersHandler.ROUTE)

  async def create_user(self, user_dict, icus, managed_icus):
    user = store.User(**user_dict)
    user_id = self.db.add_user(user)
    logging.info(f'Creating user {user_id}')

    for icu_id in icus:
      self.db.assign_user_to_icu(self.user.user_id, user_id, icu_id)
    try:
      await self.message_client.notify(
          user_id, icus, on=True, delay=self.config.scheduler.new_user_delay)
    except Exception as e:
      logging.error(f'Cannot notify MessageServer {e}')

    for icu_id in managed_icus:
      self.db.assign_user_as_icu_manager(self.user.user_id, user_id, icu_id)

  async def update_user(self, db_user, user_dict, icus, managed_icus):
    logging.info(f'Updating user {db_user.user_id}')
    user_id = db_user.user_id
    user_dict.pop('user_id', None)
    self.db.update_user(self.user.user_id, user_id, user_dict)
    await self.re_assign(db_user, icus, db_user.icus,
                         self.db.assign_user_to_icu,
                         self.db.remove_user_from_icu,
                         notify=True)
    await self.re_assign(db_user, managed_icus, db_user.managed_icus,
                         self.db.assign_user_as_icu_manager,
                         self.db.remove_manager_user_from_icu,
                         notify=False)

  def can_save(
      self, user_dict: dict, managed_icus: set, db_user: store.User) -> bool:
    is_admin = user_dict.get('is_admin', False)
    is_manager = len(managed_icus) > 0
    if not is_admin and not is_manager:
      return True

    entered_password = user_dict.get('password_hash', False)
    prior_password = db_user is not None and db_user.password_hash is not None
    has_password = entered_password or prior_password
    has_email = bool(user_dict.get('email', ''))
    return has_email and has_password

  async def save_user(self, user_dict, icus, managed_icus):
    db_user = self.db.get_user(user_dict.get('user_id', None))

    # New user admin should have password and emails
    if not self.can_save(user_dict, managed_icus, db_user):
      raise ValueError('missing email/password')

    if db_user is None:
      await self.create_user(user_dict, icus, managed_icus)
    else:
      await self.update_user(db_user, user_dict, icus, managed_icus)

  async def re_assign(self,
                      user: store.User,
                      new_icus: set,
                      user_icus: set,
                      add_fn,
                      rm_fn,
                      notify: bool = False):
    if user.user_id is None:
      return

    old_icus = set([i.icu_id for i in user_icus])
    to_add = new_icus.difference(old_icus)
    for icu_id in to_add:
      add_fn(self.user.user_id, user.user_id, icu_id)

    if notify:
      try:
        await self.message_client.notify(user.user_id, to_add, on=True)
      except Exception as e:
        logging.error(f'Cannot notify MessageServer {e}')

    to_remove = old_icus.difference(new_icus)
    for icu_id in to_remove:
      rm_fn(self.user.user_id, user.user_id, icu_id)

    if notify:
      try:
        await self.message_client.notify(user.user_id, to_remove, on=False)
      except Exception as e:
        logging.error(f'Cannot notify MessageServer {e}')
