"""Pulls data from the google sheet and adds it to the sqlite DB."""
from absl import logging

from icubam.db import store


class Synchronizer:
  """This will take data from the google sheet and put it into the sqlite DB.
  If the ICU name is already present, or the user telephone is already present,
  then it will *not* get updated.  If there is no existing row then
  a new row with the ICU or user info will get added."""
  def __init__(self, sheets_db, sqlite_db):
    self._shdb = sheets_db
    self._sqldb = sqlite_db

  def sync_icus(self):
    icus = self._shdb.get_icus()
    for row in icus.iterrows():
      icu = row[1]
      try:
        self._sqldb.upsert_icu(
          icu["icu_name"],
          icu["dept"],
          icu["city"],
          icu["lat"],
          icu["long"],
          icu["telephone"],
        )
        logging.info("Added ICU {}".format(icu["icu_name"]))
      except ValueError as e:
        logging.error(e)
        continue

  def sync_users(self):
    users = self._shdb.get_users()
    self._sqldb.execute("DELETE FROM users")
    for row in users.iterrows():
      user = row[1]
      try:
        self._sqldb.add_user(
          user["icu_name"], user["name"], user["tel"], user["description"]
        )
        logging.info("Added user {}".format(user["name"]))
      except ValueError as e:
        logging.error(e)
        continue


class StoreSynchronizer:
  """This will take data from the google sheet and put it into the sqlite DB.

  If the ICU name is already present, or the user telephone is already present,
  then it will *not* get updated.  If there is no existing row then
  a new row with the ICU or user info will get added."""
  def __init__(self, sheets_db, store_db):
    self._shdb = sheets_db
    self._store = store_db

  def prepare(self):
    # the spreadsheet has no ID, it's all keyed by name
    self._icus = {icu.name: icu for icu in self._store.get_icus()}
    self._users = {
      user.telephone: (user, user.icus)
      for user in self._store.get_users()
    }
    self._regions = {x.name: x.region_id for x in self._store.get_regions()}

    # Gather the managers and admins
    self._managers = dict()
    self._default_admin = None
    for user, icus in self._users.values():
      if user.is_admin and self._default_admin is None:
        self._default_admin = user.user_id
      for icu in user.managed_icus:
        self._managers[icu.icu_id] = user.user_id

    # Make sure there is at least one admin
    if self._default_admin is None:
      logging.info("No admin found: adding admin/admin")
      self._default_admin = self._store.add_default_admin()
    else:
      logging.info("Admin Found!")

  def sync_icus(self):
    self.prepare()
    icus_df = self._shdb.get_icus()
    icus_df.rename(columns={'icu_name': 'name'}, inplace=True)
    for _, icu in icus_df.iterrows():
      icu_dict = icu.to_dict()
      icu_name = icu_dict["name"]
      region = icu_dict.pop('region', None)
      db_icu = self._icus.get(icu_name, None)

      # Maybe create region first.
      if region is not None:
        if region not in self._regions:
          region_id = self._store.add_region(
            self._default_admin, store.Region(name=region)
          )
          self._regions[region] = region_id
          logging.info("Adding Region {}".format(region))
        icu_dict['region_id'] = self._regions[region]

      # Update icu now
      if db_icu is not None:
        manager = self._managers.get(db_icu.icu_id, self._default_admin)
        self._store.update_icu(manager, db_icu.icu_id, icu_dict)
        logging.info("Updating ICU {}".format(icu_name))
      else:
        new_icu = store.ICU(**icu_dict)
        icu_id = self._store.add_icu(self._default_admin, new_icu)
        self._store.assign_user_as_icu_manager(
          self._default_admin, self._default_admin, icu_id
        )
        logging.info("Adding ICU {}".format(icu_name))

  def sync_users(self):
    self.prepare()
    users_df = self._shdb.get_users()
    users_df.rename(columns={'tel': 'telephone'}, inplace=True)
    users_df['telephone'] = users_df['telephone'].apply(
      lambda x: x.encode('ascii', 'ignore').decode()
    )
    for _, user in users_df.iterrows():
      values = user.to_dict()
      icu_name = values.pop('icu_name')
      icu = self._icus.get(icu_name, None)
      if icu is None:
        logging.error('ICU {} not found in DB. Skipping'.format(icu_name))
        continue
      icu_id = icu.icu_id

      user_tuple = self._users.get(user['telephone'], None)
      if user_tuple is not None:
        db_user, db_user_icus = user_tuple
        logging.info("Updating user {}".format(db_user.name))
        manager_id = self._managers.get(icu_id, self._default_admin)
        self._store.update_user(manager_id, db_user.user_id, values)
        if icu_id not in [icu.icu_id for icu in db_user_icus]:
          self._store.assign_user_to_icu(manager_id, db_user.user_id, icu_id)
      else:
        try:
          self._store.add_user_to_icu(
            self._default_admin, icu_id, store.User(**values)
          )
          logging.info("Inserting user {}".format(values['name']))
        except Exception as e:
          logging.error("Cannot add user to icu: {}. Skipping".format(e))
