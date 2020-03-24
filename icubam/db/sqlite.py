"""SQLite storage backend wrapper."""
import logging
import os
import sqlite3
import time
import pandas as pd


class SQLiteDB:
  """Wraps SQLite DB for bed counts."""

  def __init__(self, db_path: str):
    """Given a token file and a sheet id, loads the sheet to be queried."""
    self._db_path = db_path

    if os.path.exists(db_path):
      self._conn = sqlite3.connect(db_path)
    else:
      self._conn = sqlite3.connect(db_path)
      self._create_table()

  def _create_table(self):
    self._conn.execute(
      """CREATE TABLE icus
                          (icu_id INTEGER NOT NULL PRIMARY KEY,
                           icu_name TEXT UNIQUE, dept TEXT, city TEXT, lat REAL,
                           long REAL, telephone TEXT )"""
    )

    self._conn.execute(
      """CREATE TABLE users
                          (user_id INTEGER NOT NULL PRIMARY KEY, icu_id INTEGER,
                           name TEXT, telephone TEXT, description TEXT,
                           UNIQUE(icu_id, telephone))"""
    )
    self._conn.execute(
      """CREATE TABLE bed_updates
                          (icu_id INTEGER, icu_name TEXT,
                          n_covid_occ TEXT, n_covid_free INTEGER,
                          n_covid_deaths TEXT, n_covid_healed INTEGER,
                          n_covid_refused TEXT, n_covid_transfered INTEGER,
                          message TEXT, update_ts integer)"""
    )
    self._conn.commit()

  def upsert_icu(
    self,
    icu_name: str,
    dept: str,
    city: str,
    lat: float,
    long: float,
    telephone: str = "NULL",
  ):
    """Add or update an ICU."""

    # If not then add:
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
    self._conn.commit()

  def add_user(
    self, icu_name: str, name: str, telephone: str, description: str
  ):
    """Add a user."""

    # Get the icu_id from icu_name:
    query = """SELECT icu_id FROM icus
               WHERE icu_name = '{icu_name}'"""
    res = pd.read_sql_query(query.format(**locals()), self._conn)
    if len(res) == 0:
      raise ValueError(f"ICU {icu_name} not present when adding user {name}.")
    icu_id = res.iloc[0]["icu_id"]

    # Insert the user:
    query = """INSERT INTO users (icu_id, name, telephone, description)
                        VALUES
                        ({icu_id}, '{name}', '{telephone}', '{description}')"""
    self._conn.execute(query.format(**locals()))
    self._conn.commit()

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
  ):
    """Updates the bedcount information for a specific hospital."""
    query = """SELECT count(icu_id) as n_icu FROM icus
               WHERE icu_id = '{icu_id}'"""
    res = pd.read_sql_query(query.format(**locals()), self._conn)
    if res.iloc[0]["n_icu"] == 0:
      raise ValueError(f"ICU {icu_id} does not exists.")

    ts = int(time.time())
    query = """INSERT INTO bed_updates (icu_id, icu_name,
                            n_covid_occ, n_covid_free,
                            n_covid_deaths, n_covid_healed,
                            n_covid_refused, n_covid_transfered,
                            update_ts)
                            VALUES
                            ({icu_id}, '{icu_name}', {n_covid_occ},
                             {n_covid_free}, {n_covid_deaths},
                             {n_covid_healed}, {n_covid_refused},
                             {n_covid_transfered}, {ts})"""

    self._conn.execute(query.format(**locals()))
    return self._conn.commit()

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

  def get_bedcount(self):
    """Returns a pandas DF of bed counts."""
    return pd.read_sql_query(
      """SELECT * FROM (SELECT * FROM bed_updates ORDER by ROWID DESC)
       AS sub GROUP BY icu_id;""",
      self._conn,
    )

  def pd_execute(self, query):
    """Run pd.read_sql_query on a query and return the DataFrame."""
    return pd.read_sql_query(query, self._conn)

  def execute(self, query):
    self._conn.execute(query)
    self._conn.commit()
