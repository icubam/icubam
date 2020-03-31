from absl import logging
from datetime import datetime
from icubam.db import store
from icubam.db import sqlite


class Migrator:
  """Migration from old db to new db.

  It has to be by name because it seems we cannot set ids directly in store.
  """
  def __init__(self, config, old_path):
    self.config = config
    self.old_db = sqlite.SQLiteDB(old_path)
    self.new_db = store.create_store_for_sqlite_db(config)
    admins = self.new_db.get_admins()
    if admins:
      self.admin_id = admins[0].user_id
    else:
      self.admin_id = self.new_db.add_default_admin()

  def run(self):
    logging.info('Migrating to {}'.format(self.config.db.sqlite_path))
    self.migrate_icus()
    self.migrate_users()
    self.migrate_bedcounts()

  def migrate_icus(self):
    icus_df = self.old_db.get_icus()
    logging.info('migrating {} icus'.format(icus_df.shape[0]))
    regions = dict()
    for _, icu_row in icus_df.iterrows():
      icu_dict = icu_row.to_dict()
      # We cannot set the id
      old_icu_id = icu_dict.pop('icu_id')
      # TODO(olivier): remove this!
      region_name = icu_dict.pop('region', 'Grand-Est')
      if region_name is not None and region_name not in regions:
        region = store.Region(name=region_name)
        region_id = self.new_db.add_region(self.admin_id, region)
        regions[region_name] = region_id
      region_id = regions.get(region_name, None)
      if region_id is not None:
        icu_dict['region_id'] = region_id
      else:
        logging.error(f"Unknown region {region_name}.")

      name = icu_dict.pop('icu_name', '-')
      icu_dict['name'] = name
      self.new_db.add_icu(self.admin_id, store.ICU(**icu_dict))
      logging.info(f'adding icus {name}')

  def migrate_users(self):
    users_df = self.old_db.get_users()
    logging.info('migrating {} users'.format(users_df.shape[0]))
    new_icus = {i.name: i for i in self.new_db.get_icus()}
    for _, user_row in users_df.iterrows():
      user_dict = user_row.to_dict()
      icu_id = user_dict.pop('icu_id', None)
      icu_name = user_dict.pop('icu_name')
      icu = new_icus.get(icu_name, None)
      if icu is None:
        logging.warning(f'cannot find {icu_name}. Skipping.')

      self.new_db.add_user_to_icu(
        self.admin_id, icu.icu_id, store.User(**user_dict))
      logging.info('Adding {} in {}'.format(user_dict['name'], icu_name))

  def migrate_bedcounts(self):
    # From oldest to newest counts
    df = self.old_db.get_bedcount(get_history=True).sort_values('update_ts')
    logging.info('migrating {} bedcounts'.format(df.shape[0]))
    new_icus = {i.name: i for i in self.new_db.get_icus()}
    for _, bc_row in df.iterrows():
      counts = bc_row.to_dict()
      icu_name = counts.pop('icu_name', None)

      counts['last_modified'] = datetime.fromtimestamp(counts.pop('update_ts'))
      counts['create_date'] = counts['last_modified']
      new_bedcount = store.BedCount(**counts)
      self.new_db.update_bed_count_for_icu(None, new_bedcount, force=True)
