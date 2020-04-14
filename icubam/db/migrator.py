from absl import logging
from icubam.db import store
import sqlite3


class Migrator:
  """Migration from old db to new db.

  It has to be by name because it seems we cannot set ids directly in store.
  """
  def __init__(self, config):
    self.config = config
    db_factory = store.create_store_factory_for_sqlite_db(config)
    self.store = db_factory.create()
    self.db = sqlite3.connect(self.config.db.sqlite_path)

  def get_table_objects(self):
    """Get the tables in our store."""
    result = []
    for key, obj in store.__dict__.items():
      try:
        if issubclass(obj, store.Base) and hasattr(obj, '__tablename__'):
          result.append(obj)
      except:
        continue
    return result

  def read_columns_from_db(self, table: str):
    curs = self.db.cursor()
    curs.execute(f"select * from {table} where 1=0;")
    return set([d[0] for d in curs.description])

  def add_column(self, table, column, column_type):
    cursor = self.db.cursor()
    cmd = f"alter table {table} add column '{column}' '{column_type}'"
    logging.info(cmd)
    cursor.execute(cmd)
    self.db.commit()
    cursor.close()

  def run(self):
    """Discover missing columns in the database and add them."""
    tables = self.get_table_objects()
    for table in tables:
      name = table.__tablename__
      db_columns = self.read_columns_from_db(name)
      store_columns = set(table.get_column_names(include_relationships=False))
      delta = store_columns - db_columns
      for column in delta:
        column_type = getattr(table, column).type.compile()
        self.add_column(name, column, column_type)
