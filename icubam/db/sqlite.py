"""SQLite storage backend wrapper."""
import logging
import os
import time
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy import Float, Integer, String

from typing import Sequence


class SQLiteDB:
  """Wraps SQLite DB for bed counts."""

  def __init__(self, db_path: str):
    """Initializes the database."""
    self._metadata = MetaData()
    self._icus = Table(
        'icus',
        self._metadata,
        Column('icu_id', Integer, primary_key=True),
        Column('icu_name', String, unique=True),
        Column('dept', String),
        Column('city', String),
        Column('lat', Float),
        Column('long', Float),
        Column('telephone', String),
    )

    self._users = Table(
        'users',
        self._metadata,
        Column('user_id', Integer, primary_key=True),
        Column('icu_id', Integer, ForeignKey('icus.icu_id')),
        Column('name', String),
        Column('telephone', String),
        Column('description', String),
        UniqueConstraint('icu_id', 'telephone'),
    )

    self._bed_updates = Table(
        'bed_updates',
        self._metadata,
        Column('icu_id', Integer),
        Column('icu_name', String),
        Column('n_covid_occ', Integer),
        Column('n_covid_free', Integer),
        Column('n_ncovid_free', Integer),
        Column('n_covid_deaths', Integer),
        Column('n_covid_healed', Integer),
        Column('n_covid_refused', Integer),
        Column('n_covid_transfered', Integer),
        Column('message', String),
        # This can be a timestamp.
        Column('update_ts', Integer),
    )

    self._engine = create_engine('sqlite:///' + db_path)
    # Only create tables that don't exist.
    self._metadata.create_all(self._engine, checkfirst=True)
    self._conn = self._engine.connect()

  def upsert_icu(
      self,
      icu_name: str,
      dept: str,
      city: str,
      lat: float,
      long: float,
      telephone: str = 'NULL',
  ):
    """Add or update an ICU."""
    # If not then add. We don't use SQLAlchemy doesn't yet support on conflict
    # update for SQLite.
    query = """INSERT INTO icus (icu_name, dept, city, lat, long, telephone)
                            VALUES
                            ('{icu_name}', '{dept}', '{city}',
                             {lat}, {long}, '{telephone}')
                            ON CONFLICT(icu_name) DO UPDATE SET
                            dept=excluded.dept,
                            city=excluded.city,
                            lat=excluded.lat,
                            long=excluded.long,
                            telephone=excluded.telephone"""
    self._conn.execute(query.format(**locals()))

  def add_user(self, icu_name: str, name: str, telephone: str,
               description: str):
    """Add a user."""

    # Get the icu_id from icu_name:
    query = """SELECT icu_id FROM icus
               WHERE icu_name = '{icu_name}'"""
    res = pd.read_sql_query(query.format(**locals()), self._conn)
    if len(res) == 0:
      raise ValueError(f"ICU {icu_name} not present when adding user {name}.")
    icu_id = res.iloc[0]['icu_id']

    # Insert the user:
    ins = self._users.insert().values(
        icu_id=icu_id, name=name, telephone=telephone, description=description)
    self._conn.execute(ins)

  def update_bedcount(
      self,
      icu_id: int,
      icu_name: str,
      n_covid_occ: int,
      n_covid_free: int,
      n_ncovid_free: int,
      n_covid_deaths: int,
      n_covid_healed: int,
      n_covid_refused: int,
      n_covid_transfered: int,
      update_ts: int = None,
  ):
    """Updates the bedcount information for a specific hospital."""
    query = """SELECT count(icu_id) as n_icu FROM icus
               WHERE icu_id = '{icu_id}'"""
    res = pd.read_sql_query(query.format(**locals()), self._conn)
    if res.iloc[0]['n_icu'] == 0:
      raise ValueError(f"ICU {icu_id} does not exists.")

    ts = update_ts or int(time.time())
    ins = self._bed_updates.insert().values(
        icu_id=icu_id,
        icu_name=icu_name,
        n_covid_occ=n_covid_occ,
        n_covid_free=n_covid_free,
        n_ncovid_free=n_ncovid_free,
        n_covid_deaths=n_covid_deaths,
        n_covid_healed=n_covid_healed,
        n_covid_refused=n_covid_refused,
        n_covid_transfered=n_covid_transfered,
        update_ts=ts)
    return self._conn.execute(ins)

  def get_icu_id_from_name(self, icu_name: str):
    # Get the icu_id from icu_name:
    query = """SELECT icu_id FROM icus
               WHERE icu_name = '{icu_name}'"""
    res = pd.read_sql_query(query.format(**locals()), self._conn)
    if len(res) == 0:
      raise ValueError(f"ICU {icu_name} not found.")
    icu_id = res.iloc[0]['icu_id']
    return icu_id

  def get_icus(self):
    """Returns a pandas DF of bed counts."""
    return pd.read_sql_query("""SELECT * FROM icus""", self._conn)

  def get_users(self):
    """Returns a pandas DF of bed counts."""
    return pd.read_sql_query(
        """SELECT users.icu_id, icu_name, name, users.telephone, description
           FROM users
           JOIN icus
           ON users.icu_id = icus.icu_id""",
        self._conn,
    )

  def get_bedcount(self, icu_ids: Sequence = None, max_ts=None):
    """Returns a pandas DF of bed counts."""
    query = """SELECT * FROM (SELECT * FROM bed_updates ORDER by ROWID DESC)
       AS sub"""

    # This is gross and should be replaced by SQL abstractions:
    if icu_ids or max_ts:
      query += ' WHERE '
      if icu_ids:
        icu_list = ','.join(map(str, icu_ids)).rstrip(',')
        query += f"""icu_id IN ({icu_list})"""
        if max_ts:
          query += ' AND '
      if max_ts:
        query += f"""update_ts < {max_ts}"""

    query += """ GROUP BY icu_id"""
    return pd.read_sql_query(query, self._conn)

  def pd_execute(self, query):
    """Run pd.read_sql_query on a query and return the DataFrame."""
    return pd.read_sql_query(query, self._conn)

  def execute(self, query):
    self._conn.execute(query)
    self._conn.commit()
