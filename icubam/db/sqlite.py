"""SQLite storage backend wrapper."""
import logging
import os
import time
import pandas as pd
from sqlalchemy import create_engine, desc, join
from sqlalchemy import Table, Column, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy import Float, Integer, String
from sqlalchemy.sql import select, text

from typing import Sequence


class SQLiteDB:
  """Wraps SQLite DB for bed counts."""

  def __init__(self, db_path: str):
    """Initializes the database."""
    self._metadata = MetaData()
    self._icus = Table(
        "icus",
        self._metadata,
        Column("icu_id", Integer, primary_key=True),
        Column("icu_name", String, unique=True),
        Column("dept", String),
        Column("city", String),
        Column("lat", Float),
        Column("long", Float),
        Column("telephone", String),
    )

    self._users = Table(
        "users",
        self._metadata,
        Column("user_id", Integer, primary_key=True),
        Column("icu_id", Integer, ForeignKey("icus.icu_id")),
        Column("name", String),
        Column("telephone", String),
        Column("description", String),
        Column("email", String),
        UniqueConstraint("icu_id", "telephone"),
    )

    self._bed_updates = Table(
        "bed_updates",
        self._metadata,
        Column("icu_id", Integer, ForeignKey("icus.icu_id")),
        Column("icu_name", String),
        Column("n_covid_occ", Integer),
        Column("n_covid_free", Integer),
        Column("n_ncovid_free", Integer),
        Column("n_covid_deaths", Integer),
        Column("n_covid_healed", Integer),
        Column("n_covid_refused", Integer),
        Column("n_covid_transfered", Integer),
        Column("message", String),
        # This can be a timestamp.
        Column("update_ts", Integer),
    )

    self._engine = create_engine("sqlite:///" + db_path)
    # Only create tables that don't exist.
    self._metadata.create_all(self._engine, checkfirst=True)
    self._conn = self._engine.connect()
    self.maybe_migrate()

  def maybe_migrate(self):
    """Migrates database tables and columns."""
    conn = self._conn
    # SQLite doesn't support IF NOT EXISTS. Instead, we ignore the exception
    # which arises if the field is present.
    try:
      conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR"))
    except Exception:
      pass

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
    # If not then add. We don't use SQLAlchemy as it doesn't yet support on
    # conflict update for SQLite.
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

  def add_user(self,
               icu_name: str,
               name: str,
               telephone: str,
               description: str,
               email: str = "NULL"):
    """Add a user."""

    # Get the icu_id from icu_name:
    icus = self._icus.c
    s = select([icus.icu_id]).where(icus.icu_name == icu_name)
    res = self._conn.execute(s).fetchone()
    if not res:
      raise ValueError(f"ICU {icu_name} not present when adding user {name}.")
    icu_id = res["icu_id"]

    # Insert the user:
    ins = self._users.insert().values(
        icu_id=icu_id,
        name=name,
        telephone=telephone,
        description=description,
        email=email)
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
    if res.iloc[0]["n_icu"] == 0:
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
        update_ts=ts,
    )
    return self._conn.execute(ins)

  def get_icu_id_from_name(self, icu_name: str):
    # Get the icu_id from icu_name:
    query = """SELECT icu_id FROM icus
               WHERE icu_name = '{icu_name}'"""
    res = pd.read_sql_query(query.format(**locals()), self._conn)
    if len(res) == 0:
      raise ValueError(f"ICU {icu_name} not found.")
    icu_id = res.iloc[0]["icu_id"]
    return icu_id

  def get_icus(self):
    """Returns a pandas DF of bed counts."""
    return pd.read_sql_query("""SELECT * FROM icus""", self._conn)

  def get_users(self):
    """Returns a pandas DF of users."""
    users = self._users
    icus = self._icus
    stmt = select([
        users.c.icu_id,
        icus.c.icu_name,
        users.c.name,
        users.c.telephone,
        users.c.description,
        users.c.email,
    ]).select_from(users.join(icus))
    return pd.read_sql_query(stmt, self._conn)

  def get_bedcount(self, icu_ids: Sequence = None, max_ts=None):
    """Returns a pandas DF of bed counts."""
    sub = select([self._bed_updates]).order_by(desc(text("ROWID")))
    if icu_ids:
      sub = sub.where(self._bed_updates.c.icu_id.in_(icu_ids))
    if max_ts:
      # Equilavent to self._bed_updates.c.update_ts < max_ts, but this doesn't
      # seem to work properly (i.e. rows are not filtered).
      sub = sub.where(text(f"""update_ts < {max_ts}"""))
    query = select([sub]).group_by("icu_id")
    return pd.read_sql_query(query, self._conn)

  def pd_execute(self, query):
    """Run pd.read_sql_query on a query and return the DataFrame."""
    return pd.read_sql_query(query, self._conn)

  def execute(self, query):
    self._conn.execute(query)
    self._conn.commit()
