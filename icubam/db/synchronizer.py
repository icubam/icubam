"""Pulls data from the google sheet and adds it to the sqlite DB."""
from absl import logging

from icubam.db import gsheets
from icubam.db import sqlite
from icubam.db import store


class Synchronizer:
  """This will take data from the google sheet and put it into the sqlite DB.

  If the ICU name is already present, or the user telephone is already present,
  then it will *not* get updated.  If there is no existing row then
  a new row with the ICU or user info will get added."""

  def __init__(self, sheets_db, store_db):
    self._shdb = sheets_db
    self._store = store_db

    # the spreadsheet has no ID, it's all keyed by name
    self._icus = {icu.name: icu for icu in self._store.get_icus()}
    self._users = {user.telephone: user for user in self._store.get_users()}

    # Gather the managers and admins
    self._managers = dict()
    self._default_admin = None
    for user in self._users.values():
      if user.is_admin and self._default_admin is None:
        self._default_admin = user.user_id
      for icu in user.managed_icus:
        self._manager[icu.icu_id] = user.user_id

    # Make sure there is at least one admin
    if self._default_admin is None:
      logging.info("No admin found: adding admin/admin")
      self._default_admin = self._store.add_default_admin()
    else:
      logging.info("Admin Found!")

  def sync_icus(self):
    icus_df = self._shdb.get_icus()
    icus_df.rename(columns={'icu_name': 'name'}, inplace=True)
    for _, icu in icus_df.iterrows():
      icu_name = icu["name"]
      db_icu = self._icus.get(icu_name, None)
      if db_icu is not None:
        self._store.update_icu(
          self._managers[db_icu.icu_id], db_icu.icu_id, icu)
        logging.info("Updating ICU {}".format(icu_name))
      else:
        self._store.add_icu(self._default_admin, store.ICU(**icu.to_dict()))
        logging.info("Adding ICU {}".format(icu_name))

  def sync_users(self):
    users_df = self._shdb.get_users()
    icus_df.rename(columns={'tel': 'telephone'}, inplace=True)
    for _, user in users.iterrows():
      values = user.to_dict()
      icu_name = values.pop('icu_name')
      icu_id = self._icus.get(icu_name, None)
      db_user = self._users.get(user['name'], None)

      if db_user is not None:
        icuid = db_user.icus[0] if db_user.icus else None
        m_id = self._default_admin if icuid is None else self._managers[icuid]

        self._store.update_user(m_id, db_user.user_id, **values)
        if icu_id not in db_users.icus:
          self._store.assign_user_to_icu(m_id, db_user.user_ud, icu_id)
        logging.info("Updating user {}".format(db_user.name))
      else:
        self.store.add_user_to_icu(
          self._default_admin, icu_id, User(**user.to_dict()))
