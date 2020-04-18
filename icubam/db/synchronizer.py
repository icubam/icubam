"""Synchronize the internal store from an external source."""
import copy
from collections import defaultdict
from typing import TextIO

import pandas as pd
from absl import logging
from dateutil import tz

from icubam.db import store

# These columns need to be provided, most can be set to None if there is no
# value, however columns that are used to create joins such as icu_name or
# ICU_COLUMNS['name'] will throw an error if they are None or not aligned with
# existing elements in the store.
ICU_DTYPE = {
  'name': 'string',
  'legal_id': 'string',
  'country': 'string',
  'region': 'string',
  'dept': 'string',
  'city': 'string',
  'lat': 'string',
  'long': 'string',
  'telephone': 'string'
}
ICU_COLUMNS = list(ICU_DTYPE.keys())
USER_COLUMNS = ['icu_name', 'name', 'telephone', 'description']
BC_COLUMNS = [
  'icu_name', 'n_covid_occ', 'n_covid_free', 'n_ncovid_occ', 'n_ncovid_free',
  'n_covid_deaths', 'n_covid_healed', 'n_covid_refused', 'n_covid_transfered',
  'create_date'
]


class StoreSynchronizer:
  """This will take data from pandas DFs and insert it into the store.

  If ICUs or Users already exists, their data will get updated.
  If there is no existing row then a new row with the ICU or user info will get added.
  """
  def __init__(self, store_db):
    self.db = store_db

  def prepare(self):
    # Gather the managers and admins already present
    users = {user.telephone: (user, user.icus) for user in self.db.get_users()}
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
      self._default_admin = self.db.add_default_admin()
    else:
      logging.info("Admin Found!")

  def sync_icus(self, icus_df, force_update=False):
    self.prepare()

    # pandas sometimes maps missing values (for example in CSV files) to NA
    # but NA values are rejected by our SQL layer, so we replace them with None
    icus_df = icus_df.replace({pd.NA: None})

    for _, icu in icus_df.iterrows():
      icu_dict = icu.to_dict()
      icu_name = icu_dict["name"]
      region = icu_dict.pop('region', None)
      db_icu = self.db.get_icu_by_name(icu_name)
      if db_icu is not None and not force_update:
        continue

      # Maybe create region first.
      if region is not None:
        regions = {x.name: x.region_id for x in self.db.get_regions()}
        if region not in regions:
          self.db.add_region(self._default_admin, store.Region(name=region))
          logging.info("Adding Region {}".format(region))
        icu_dict['region_id'] = self.db.get_region_by_name(region).region_id

      # If an ICU exists with the same name, update:
      if db_icu is not None:
        manager = self._managers.get(db_icu.icu_id, [
          self._default_admin,
        ])[0]
        logging.info(manager)
        self.db.update_icu(manager, db_icu.icu_id, icu_dict)
        logging.info("Updating ICU {}".format(icu_name))
      # Or insert new ICU:
      else:
        new_icu = store.ICU(**icu_dict)
        icu_id = self.db.add_icu(self._default_admin, new_icu)
        self.db.assign_user_as_icu_manager(
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
      icu = self.db.get_icu_by_name(icu_name)
      if icu is None:
        raise ValueError('ICU {} not found in DB. Skipping'.format(icu_name))
      icu_id = icu.icu_id

      db_user = self.db.get_user_by_phone(user['telephone'])
      if db_user is not None and not force_update:
        continue
      # Update the user:
      if db_user is not None:
        db_user_icus = db_user.icus
        logging.info(f"Updating user {db_user.name}.")
        manager_id = self._managers.get(icu_id, self._default_admin)[0]
        self.db.update_user(manager_id, db_user.user_id, values)
        if icu_id not in [icu.icu_id for icu in db_user_icus]:
          self.db.assign_user_to_icu(manager_id, db_user.user_id, icu_id)
      # Or insert new user:
      else:
        try:
          self.db.add_user_to_icu(
            self._default_admin, icu_id, store.User(**values)
          )
          logging.info("Inserting user {}".format(values['name']))
        except Exception as e:
          logging.error("Cannot add user to icu: {}. Skipping".format(e))

  def sync_bed_counts(self, bedcounts_df, user=None):
    self.prepare()
    bedcounts_df = bedcounts_df[BC_COLUMNS]

    # First check that all ICUs exist:
    icu_names = set(bedcounts_df['icu_name'].unique())
    db_icus = dict((icu.name, icu) for icu in self.db.get_icus())

    # Make sure each bedcount has an existent ICU:
    icu_diff = icu_names - set(db_icus.keys())
    if len(icu_diff) > 0:
      raise KeyError(f"Missing ICUs in DB: {icu_diff}. Please add them first.")

    # Now we are sure all ICUs are present so we can insert without checking:
    for idx, bc in bedcounts_df.iterrows():
      if bc['create_date'].tzinfo != tz.tzutc():
        raise ValueError(
          "Timestamps must be in UTC, got {}".format(bc['create_date'].tzinfo)
        )
      item = bc.to_dict()
      # Replace icu_name with corresponding ID:
      item['icu_id'] = db_icus[item['icu_name']].icu_id
      del item['icu_name']
      item['last_modified'] = item['create_date']
      # import ipdb; ipdb.set_trace()
      logging.info(f"Inserting BedCount: {item} into DB.")
      self.db.update_bed_count_for_icu(
        user, store.BedCount(**item), force=not user
      )


class CSVSynchronizer(StoreSynchronizer):
  """Ingests CSV TextIO objects into datastore."""
  def sync_icus_from_csv(self, csv_contents: TextIO, force_update=False):
    """Check that columns correspond, insert into a DF and sychronize."""
    icus_df = pd.read_csv(csv_contents, dtype=ICU_DTYPE)
    col_diff = set(ICU_COLUMNS) - set(icus_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")
    self.sync_icus(icus_df, force_update)
    return icus_df.shape[0]

  def sync_users_from_csv(self, csv_contents: TextIO, force_update=False):
    """Check that columns correspond, insert into a DF and synchronize."""
    users_df = pd.read_csv(csv_contents)
    col_diff = set(USER_COLUMNS) - set(users_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")
    self.sync_users(users_df, force_update)
    return users_df.shape[0]

  def sync_bedcounts_from_csv(self, csv_contents: TextIO, force_update=False):
    """Check that columns correspond, insert into a DF and synchronize."""
    bedcounts_df = pd.read_csv(csv_contents)
    col_diff = set(BC_COLUMNS) - set(bedcounts_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")
    self.sync_users(bedcounts_df, force_update)
    return bedcounts_df.shape[0]

  def export_icus(self) -> TextIO:
    db_cols = copy.copy(ICU_COLUMNS)
    db_cols.remove('region')
    icus_pd = store.to_pandas(self.db.get_icus(), max_depth=1)
    out_pd = icus_pd[db_cols].copy()
    out_pd['region'] = icus_pd['region_name']
    out_pd = out_pd[ICU_COLUMNS]
    return out_pd.to_csv(index=False)

  def export_all_bedcounts(self) -> TextIO:
    raise NotImplementedError("Not yet implemented.")

  def export_users(self, csv_file_path: str):
    raise NotImplementedError("Cannot export users to CSV.")


class CSVPreprocessor(CSVSynchronizer):
  """Set of helper functions to preprocess non-standard CSVs."""

  ROR_COLUMNS_MAP = {
    'COD_ROR_EG': 'ror_code',
    'NOM': 'icu_name',
    'DHM_SAI': 'create_date',
    'NBR_LIT_DSP': 'n_covid_free',
    'NBR_LIT_INS': 'n_covid_tot'
  }

  def sync_bedcounts_ror_idf(self, csv_contents: TextIO, user=None):
    """Sync bedcount CSVs from IdF RoR uplink."""
    bedcounts_df = pd.read_csv(csv_contents)
    col_diff = set(self.ROR_COLUMNS_MAP.keys()) - set(bedcounts_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")

    # Remap columns and delete or default certain ones:
    bc = bedcounts_df
    bc.replace(self.ROR_COLUMNS_MAP)
    bc['n_covid_occ'] = bc['n_covid_tot'] - bc['n_covid_free']
    bc[[
      'n_covid_deaths', 'n_covid_healed', 'n_covid_refused',
      'n_covid_transfered'
    ]] = None

    # Parse datetime and convert to UTC:
    bc['create_date'] = pd.to_datetime(
      bc['create_date']
    ).dt.tz_localize("Europe/Paris").dt.tz_convert(tz.tzutc())
    self.sync_bed_counts(bc, user)
