"""Synchronize the internal store from an external source."""
import copy
from collections import defaultdict
from typing import TextIO

import pandas as pd
import pytz
from absl import logging

from icubam.db import store

ICU_COLUMNS = ['name', 'region', 'dept', 'city', 'lat', 'long', 'telephone']
USER_COLUMNS = ['icu_name', 'name', 'telephone', 'description']
BC_COLUMNS = [
  'icu_name', 'n_covid_occ', 'n_covid_free', 'n_ncovid_occ', 'n_ncovid_free',
  'n_covid_deaths', 'n_covid_healed', 'n_covid_refused', 'n_covid_transfered',
  'timestamp'
]


class StoreSynchronizer:
  """This will take data from pandas DFs and insert it into the store.

  If ICUs or Users already exists, their data will get updated.
  If there is no existing row then a new row with the ICU or user info will get added.
  """
  def __init__(self, store_db):
    self._store = store_db

  def prepare(self):
    # Gather the managers and admins already present
    users = {
      user.telephone: (user, user.icus)
      for user in self._store.get_users()
    }
    self._managers = defaultdict(list)
    self._default_admin = None
    for user, icus in users.values():
      if user.is_admin and self._default_admin is None:
        self._default_admin = user.user_id
      for icu in user.managed_icus:
        self._managers[icu.icu_id].append(user.user_id)

    # Make sure there is at least one admin:
    if self._default_admin is None:
      logging.info("No admin found: adding admin/admin")
      self._default_admin = self._store.add_default_admin()
    else:
      logging.info("Admin Found!")

  def sync_icus(self, icus_df, force_update=False):
    self.prepare()

    for _, icu in icus_df.iterrows():
      icu_dict = icu.to_dict()
      icu_name = icu_dict["name"]
      region = icu_dict.pop('region', None)
      db_icu = self._store.get_icu_by_name(icu_name)
      if db_icu is not None and not force_update:
        continue

      # Maybe create region first.
      if region is not None:
        regions = {x.name: x.region_id for x in self._store.get_regions()}
        if region not in regions:
          region_id = self._store.add_region(
            self._default_admin, store.Region(name=region)
          )
          logging.info("Adding Region {}".format(region))
        icu_dict['region_id'] = self._store.get_region_by_name(
          region
        ).region_id

      # If an ICU exists with the same name, update:
      if db_icu is not None:
        manager = self._managers.get(db_icu.icu_id, self._default_admin)[0]
        logging.info(manager)
        self._store.update_icu(manager, db_icu.icu_id, icu_dict)
        logging.info("Updating ICU {}".format(icu_name))
      # Or insert new ICU:
      else:
        new_icu = store.ICU(**icu_dict)
        icu_id = self._store.add_icu(self._default_admin, new_icu)
        self._store.assign_user_as_icu_manager(
          self._default_admin, self._default_admin, icu_id
        )
        logging.info("Adding ICU {}".format(icu_name))

  def sync_users(self, users_df, force_update=False):
    self.prepare()
    users_df = users_df[USER_COLUMNS]
    users_df['telephone'] = users_df['telephone'].apply(
      lambda x: str(x).encode('ascii', 'ignore').decode()
    )
    for _, user in users_df.iterrows():
      values = user.to_dict()
      icu_name = values.pop('icu_name')
      icu = self._store.get_icu_by_name(icu_name)
      if icu is None:
        raise ValueError('ICU {} not found in DB. Skipping'.format(icu_name))
      icu_id = icu.icu_id

      db_user = self._store.get_user_by_phone(user['telephone'])
      if db_user is not None and not force_update:
        continue
      # Update the user:
      if db_user is not None:
        db_user_icus = db_user.icus
        logging.info(f"Updating user {db_user.name}.")
        manager_id = self._managers.get(icu_id, self._default_admin)[0]
        self._store.update_user(manager_id, db_user.user_id, values)
        if icu_id not in [icu.icu_id for icu in db_user_icus]:
          self._store.assign_user_to_icu(manager_id, db_user.user_id, icu_id)
      # Or insert new user:
      else:
        try:
          self._store.add_user_to_icu(
            self._default_admin, icu_id, store.User(**values)
          )
          logging.info("Inserting user {}".format(values['name']))
        except Exception as e:
          logging.error("Cannot add user to icu: {}. Skipping".format(e))

  def sync_bed_counts(self, bedcounts_df, user=None):
    raise NotImplementedError("WIP")
    bedcounts_df = bedcounts_df[BC_COLUMNS]

    # First check that all ICUs exist:
    icu_names = set(bedcounts_df['icu_name'].unique())
    db_icus = dict((icu.name, icu) for icu in self.db.get_icus())

    # Make sure each bedcount has an existent ICU:
    icu_diff = icu_names - set(db_icus.keys())
    if icu_diff is not None:
      raise KeyError("Missing ICUs in DB: {icu_diff}. Please add them first.")

    # Now we are sure all ICUs are present so we can insert without checking:
    for bc in bedcounts_df.iterrows():
      if bc['timestamp'].tzinfo != pytz.utc:
        raise ValueError(
          "Timestamps must be in UTC, got {}".forma(bc['timestamp'].tzinfo)
        )
      item = bc.to_dict()
      self.db.update_bed_count_for_icu(
        user, store.BedCount(**item), force=not user
      )


class CSVSynchcronizer(StoreSynchronizer):
  """Ingests CSV TextIO objects into datastore."""
  def sync_icus_from_csv(self, csv_contents: TextIO, force_update=False):
    """Check that columns correspond, insert into a DF and sychronize."""
    icus_df = pd.read_csv(csv_contents)
    col_diff = set(ICU_COLUMNS) - set(icus_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")
    self.sync_icus(icus_df, force_update)

  def sync_users_from_csv(self, csv_contents: TextIO, force_update=False):
    """Check that columns correspond, insert into a DF and synchronize."""
    users_df = pd.read_csv(csv_contents)
    col_diff = set(USER_COLUMNS) - set(users_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")
    self.sync_users(users_df, force_update)

  def export_icus(self) -> TextIO:
    db_cols = copy.copy(ICU_COLUMNS)
    db_cols.remove('region')
    icus_pd = store.to_pandas(self._store.get_icus(), max_depth=1)
    out_pd = icus_pd[db_cols].copy()
    out_pd['region'] = icus_pd['region_name']
    out_pd = out_pd[ICU_COLUMNS]
    return out_pd.to_csv(index=False)

  def export_all_bedcounts(self) -> TextIO:
    raise NotImplementedError("Not yet implemented.")

  def export_users(self, csv_file_path: str):
    raise NotImplementedError("Cannot export users to CSV.")
