"""Data store for ICUBAM."""
from absl import logging
from contextlib import contextmanager
import dataclasses
from datetime import datetime
import hashlib
import pandas as pd
from sqlalchemy import create_engine, desc, func
from sqlalchemy import Column, Table
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean, Float, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import text
from typing import Iterable, Optional, Tuple
import uuid


class Base(object):
  """Base with helper methods."""

  def _get_column_names(self):
    """Returns the columns of the table."""
    return list(self.__mapper__.columns.keys())

  def to_dict(self):
    """Turns a Base instance into a dictionary."""
    columns = self._get_column_names()
    result = {}
    for col in columns:
      result[col] = getattr(self, col)
    return result


Base = declarative_base(cls=Base)

# Users that are assigned to an ICU.
icu_users = Table(
    "icu_users", Base.metadata,
    Column("icu_id", ForeignKey("icus.icu_id"), primary_key=True),
    Column("user_id", ForeignKey("users.user_id"), primary_key=True))

# Users that can manage an ICU.
icu_managers = Table(
    "icu_managers", Base.metadata,
    Column("icu_id", ForeignKey("icus.icu_id"), primary_key=True),
    Column("user_id", ForeignKey("users.user_id"), primary_key=True))


class User(Base):
  """Represents a user."""
  __tablename__ = "users"

  user_id = Column(Integer, primary_key=True)
  name = Column(String)
  # Telephone and email should be unique for each user.
  # TODO(olivier): removing for now.
  telephone = Column(String)  # , unique=True)
  email = Column(String)
  description = Column(String)
  # Strong hash of the password. Used for admin and manager users.
  password_hash = Column(String)
  # Used for regular users for passwordless access.
  access_salt = Column(String)
  is_active = Column(Boolean, default=True, server_default=text("1"))
  is_admin = Column(Boolean, default=False, server_default=text("0"))
  # Locale of the user for translations.
  locale = Column(String)
  # One of {email, sms}.
  message_type = Column(String, default="email")

  create_date = Column(DateTime, default=func.now())
  last_modified = Column(DateTime, default=func.now(), onupdate=func.now())

  # ICUs that the user is assigned to.
  icus = relationship("ICU", secondary=icu_users, back_populates="users")
  # ICUs that the user manages.
  managed_icus = relationship(
      "ICU", secondary=icu_managers, back_populates="users")


class Region(Base):
  """Represents a region. Each ICU belongs to a particular region."""
  __tablename__ = "regions"

  region_id = Column(Integer, primary_key=True)
  name = Column(String)

  create_date = Column(DateTime, default=func.now())
  last_modified = Column(DateTime, default=func.now(), onupdate=func.now())

  # ICUs in the region.
  icus = relationship("ICU", back_populates="region")


class BedCount(Base):
  """Bed count for an ICU at a point in time."""
  __tablename__ = "bed_counts"

  # ORM requires having a primary key.
  rowid = Column(Integer, primary_key=True)
  icu_id = Column(Integer, ForeignKey("icus.icu_id"))
  n_covid_occ = Column(Integer)
  n_covid_free = Column(Integer)
  n_ncovid_occ = Column(Integer)
  n_ncovid_free = Column(Integer)
  n_covid_deaths = Column(Integer)
  n_covid_healed = Column(Integer)
  n_covid_refused = Column(Integer)
  n_covid_transfered = Column(Integer)
  message = Column(String)

  # Date and time of the bed count.
  create_date = Column(DateTime, default=func.now())
  last_modified = Column(DateTime, default=func.now(), onupdate=func.now())

  # ICU of the bed count.
  icu = relationship("ICU", back_populates="bed_counts")


class ICU(Base):
  """Represents an ICU."""
  __tablename__ = "icus"

  icu_id = Column(Integer, primary_key=True)
  # Region that the ICU belongs to.
  region_id = Column(Integer, ForeignKey("regions.region_id"))
  name = Column(String)
  # Geographical location of the ICU. These are orthogonal to the region, which
  # is a more abstract grouping.
  dept = Column(String)
  city = Column(String)
  country = Column(String)
  lat = Column(Float)
  long = Column(Float)
  telephone = Column(String)
  is_active = Column(Boolean, default=True, server_default=text("1"))

  create_date = Column(DateTime, default=func.now())
  last_modified = Column(DateTime, default=func.now(), onupdate=func.now())

  # Region of the ICU.
  region = relationship("Region", back_populates="icus")
  # History of bed counts.
  bed_counts = relationship(
      "BedCount", back_populates="icu", order_by=BedCount.last_modified)
  # Users that are assigned to the ICU.
  users = relationship("User", secondary=icu_users, back_populates="icus")
  # Users that can manage the ICU.
  managers = relationship("User", secondary=icu_managers, back_populates="icus")


class ExternalClient(Base):
  "Represents an external client that can access ICUBAM data." ""
  __tablename__ = "external_clients"

  external_client_id = Column(Integer, primary_key=True)
  name = Column(String)
  email = Column(String)
  telephone = Column(String)
  # Strong hash of the access key. It should be unique.
  access_key_hash = Column(String, unique=True)
  # If set, denotes the date that the access key expires.
  expiration_date = Column(DateTime)
  is_active = Column(Boolean, default=True, server_default=text("1"))

  create_date = Column(DateTime, default=func.now())
  last_modified = Column(DateTime, default=func.now(), onupdate=func.now())

  @property
  def access_key_valid(self):
    """Returns true if the access key is valid."""
    return self.expiration_date is None or self.expiration_date > datetime.now()


@dataclasses.dataclass
class AccessKey(object):
  """Access key together with its hash."""
  key: str
  key_hash: str


class Store:
  """Provides high level access to the data store."""

  def __init__(self, engine, salt=""):
    if salt is None:
      logging.warning("DB_SALT is not defined. Falling back to default")
      salt = ""

    Base.metadata.create_all(engine)
    self._session = sessionmaker(bind=engine)
    self._salt = salt.encode()

  @contextmanager
  def session_scope(self, session=None):
    """Provide a transactional scope around a series of operations."""
    session = session or self._session()
    try:
      yield session
      session.commit()
    except:
      session.rollback()
      raise
    finally:
      session.close()

  def _get_user(self, session, user_id: int) -> Optional[User]:
    """Returns the user with the specified ID."""
    return session.query(User).filter(User.user_id == user_id).one_or_none()

  def _is_admin(self, session, user_id: int) -> bool:
    """Returns true if the user with the specified ID is an admin."""
    user = self._get_user(session, user_id)
    return user and user.is_admin

  # ICU related methods.

  def add_icu(self, admin_user_id: int, icu: ICU) -> int:
    """Adds a new ICU.

    Args:
      admin_user_id: ID of the admin user.
      icu: an ICU object. icu_id field should not be set.

    Returns:
      ID of the ICU.
    """
    if icu.icu_id:
      raise ValueError("ID of a new ICU should not be set.")
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admins can add a new ICU.")
      session.add(icu)
      session.commit()
      return icu.icu_id

  def get_icu(self, icu_id: int) -> Optional[ICU]:
    """Returns the ICU with the specified ID."""
    return self._session().query(ICU).filter(ICU.icu_id == icu_id).one_or_none()

  def get_icus(self) -> Iterable[ICU]:
    """Returns all users, e.g. sync. Do not use in user facing code."""
    return self._session().query(ICU).all()

  def update_icu(self, manager_user_id: int, icu_id: int, values):
    """Updates an existing ICU.

    Args:
      manager_user_id: ID of the user that manages the ICU.
      icu_id: ID of the ICU.
      values: a dict of ICU fields to update.
    """
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("User does not own the ICU.")
    with self.session_scope() as session:
      session.query(ICU).filter(ICU.icu_id == icu_id).update(values)

  def manages_icu(self, user_id: int, icu_id: int) -> bool:
    """Returns true if the user manages the ICU with the specified ID."""
    with self.session_scope() as session:
      if self._is_admin(session, user_id):
        return True
      return session.query(icu_managers).filter(
          icu_managers.c.user_id == user_id).filter(
              icu_managers.c.icu_id == icu_id).count() == 1

  def enable_icu(self, manager_user_id: int, icu_id: int, is_active=True):
    """Enables the ICU with the specified ID."""
    self.update_icu(manager_user_id, icu_id, {"is_active": is_active})

  def disable_icu(self, manager_user_id: int, icu_id: int):
    """Disables the ICU with the specified ID."""
    self.enable_icu(manager_user_id, icu_id, False)

  def assign_user_as_icu_manager(self, admin_user_id: int, manager_user_id: int,
                                 icu_id: int):
    """Assigns the specified user as a manager of an ICU."""
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admin users can assign managers to ICUs.")
      session.execute(icu_managers.insert().values(
          user_id=manager_user_id, icu_id=icu_id))

  def get_managed_icus(self, manager_user_id: int) -> Iterable[ICU]:
    """Returns the list of ICUs managed by the user."""
    session = self._session()
    # Admins can manage all ICUs.
    if self._is_admin(session, manager_user_id):
      return session.query(ICU).all()
    user = self._get_user(session, manager_user_id)
    return user.managed_icus if user else []

  # User related methods.

  def add_default_admin(self) -> int:
    """Creates a default 'admin/admin' user."""
    name = "admin"
    hash = self.get_password_hash(name)
    return self.add_user(
        User(name=name, email=name, password_hash=hash, is_admin=True))

  def add_user(self, user: User) -> int:
    """Adds a new user and returns its ID.

    Args:
      user: a User object. user_id field should not be set.

    Returns:
      ID of the user.
    """
    with self.session_scope() as session:
      session.add(user)
      session.commit()
      return user.user_id

  def add_user_to_icu(self, manager_user_id: int, icu_id: int,
                      user: User) -> int:
    """Adds a new user and assigns it with the specified ICU.

    Args:
      manager_user_id: ID of the user that manages the ICU.
      icu_id: ID of the ICU that the user will be assigned to.
      user: a User object. user_id field should not be set.

    Returns:
      ID of the user.
    """
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("User does not own the ICU.")
    user_id = self.add_user(user)
    self.assign_user_to_icu(manager_user_id, user_id, icu_id)
    return user_id

  def get_user(self, user_id: int) -> User:
    """Returns the user with the specified ID."""
    return self._get_user(self._session(), user_id)

  def get_users(self) -> Iterable[User]:
    """Returns all users, e.g. sync. Do not use in user facing code."""
    return self._session().query(User).all()

  def get_admins(self) -> Iterable[User]:
    """Returns all admins, e.g. sync. Do not use in user facing code."""
    return self._session().query(User).filter(User.is_admin).all()

  def update_user(self, manager_user_id: int, user_id: int, values):
    """Updates an existing user without changing the assigned ICUs.

    Args:
      manager_user_id: ID of an admin user or a user that manages one of the
        ICUs that the user is assigned to.
      user_id: ID of the user.
      values: a dict of user fields to update.
    """
    if not self.manages_user(manager_user_id, user_id):
      raise ValueError(
          "Only users associated with managed ICUs can be updated.")
    with self.session_scope() as session:
      session.query(User).filter(User.user_id == user_id).update(values)

  def assign_user_to_icu(self, manager_user_id: int, user_id: int, icu_id: int):
    """Assigns the specified user to an ICU."""
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("Only managers can assign users to a ICU.")
    with self.session_scope() as session:
      session.execute(icu_users.insert().values(user_id=user_id, icu_id=icu_id))

  def remove_user_from_icu(self, manager_user_id: int, user_id: int,
                           icu_id: int):
    """Removes an existing assignment of user to an ICU."""
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("Only managers can remove users from an ICU.")
    with self.session_scope() as session:
      session.execute(icu_users.delete().where(
          icu_users.c.user_id == user_id).where(icu_users.c.icu_id == icu_id))

  def enable_user(self, manager_user_id: int, user_id: int, is_active=True):
    """Enables the user with the specified ID."""
    self.update_user(manager_user_id, user_id, {"is_active": is_active})

  def disable_user(self, manager_user_id: int, user_id: int):
    """Disables the user with the specified ID."""
    self.enable_user(manager_user_id, user_id, False)

  def manages_user(self, manager_user_id: int, user_id: int) -> bool:
    """Returns true if the manager user can manage the user."""
    with self.session_scope() as session:
      if self._is_admin(session, manager_user_id):
        return True
      return session.query(icu_managers.c.user_id, icu_users.c.user_id).filter(
          icu_managers.c.user_id == manager_user_id).join(
              icu_users, icu_managers.c.icu_id).filter(
                  icu_users.c.user_id == user_id).count() == 1

  def get_managed_users(self, manager_user_id: int) -> Iterable[User]:
    """Returns the list of users managed by the manager user."""
    icus = self.get_managed_icus(manager_user_id)
    if not icus:
      return []
    icu_ids = [icu.icu_id for icu in icus]
    return self._session().query(User).join(icu_users).filter(
        icu_users.c.icu_id.in_(icu_ids)).all()

  # Authentication related methods.

  def get_password_hash(self, password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf8"), self._salt,
                               100000).hex()

  def auth_user(self, email: str, password: str) -> int:
    """Authenticates a user using email and password.

    Args:
      email: Email of the user.
      password: Password of the user.

    Returns:
      ID of the user if the email and (hash of the) password matches.
    """
    return self._session().query(
        User.user_id).filter(User.email == email).filter(
            User.password_hash == self.get_password_hash(password)).scalar()

  def auth_user_by_token(token: str) -> int:
    """Authenticates a user using a token.

    Returns:
      ID of the user with the matching token.
    """
    raise NotImplementedError()

  # Region related methods.

  def add_region(self, admin_user_id: int, region: Region) -> int:
    """Adds a new region.

    Args:
      admin_user_id: ID of the admin user.
      region: a Region object. region_id field should not be set.

    Returns:
      ID of the region.
    """
    if region.region_id:
      return ValueError("ID of a new region should not be set.")
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admins can add a new region.")
      session.add(region)
      session.commit()
      return region.region_id

  def get_region(self, region_id: int) -> Optional[Region]:
    """Returns the region with the specified ID."""
    return self._session().query(Region).filter(
        Region.region_id == region_id).one_or_none()

  def get_regions(self) -> Iterable[Region]:
    """Returns the list of regions."""
    return self._session().query(Region).all()

  def update_region(self, admin_user_id: int, region_id: int, values):
    """Updates an existing region.

    Args:
      admin_user_id: ID of the admin user.
      region_id: ID of the region.
      values: a dict of Region fields to update.
    """
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admins can update a region.")
      session.query(Region).filter(Region.region_id == region_id).update(values)

  def get_icus_in_region(region_id: int) -> Iterable[ICU]:
    """Returns the ICUs in the region with the specified ID."""
    return self._session().query(Region).filter(
        Region.region_id == region_id).one().icus

  # Bed count related methods.

  def get_bed_counts(self, max_date = None) -> Iterable[BedCount]:
    """Returns all users, e.g. sync. Do not use in user facing code."""
    query = self._session().query(BedCount)
    if max_date is not None:
      query = query.filter(BedCount.last_modified <= max_date)
    return query.all()

  def get_bed_count_for_icu(self, icu_id: int) -> Optional[BedCount]:
    """Returns the latest bed count for the ICU with the specified ID."""
    return self._session().query(BedCount).filter(
        BedCount.icu_id == icu_id).order_by(desc(BedCount.create_date)).first()

  def update_bed_count_for_icu(self,
                               user_id: int,
                               bed_count: BedCount,
                               force=False):
    """Updates the latest bed count for the specified ICU."""
    if not self.can_edit_bed_count(user_id, bed_count.icu_id) and not force:
      raise ValueError("User cannot edit bed count for the ICU.")
    with self.session_scope() as session:
      session.add(bed_count)

  def can_edit_bed_count(self, user_id: int, icu_id: int) -> bool:
    """Returns true if the user can edit the bed count for the specified ICU."""
    with self.session_scope() as session:
      if self._is_admin(session, user_id):
        return True
      return session.query(icu_users).filter(
          icu_users.c.user_id == user_id).filter(
              icu_users.c.icu_id == icu_id).count() == 1

  def get_visible_bed_counts_for_user(self,
                                      user_id,
                                      max_date: datetime = None,
                                      force=False
                                     ) -> Iterable[BedCount]:
    """Returns the latest bed counts of ICS that are visible to the user.

    Admin users can view all ICUs. For other users, only ICUs that are in the
    same regions as the ICUs that they are assigned to will be visible.
    """
    session = self._session()
    # Bed counts in reverse chronological order.
    sub = session.query(BedCount.rowid, BedCount.icu_id,
                        BedCount.create_date).order_by(
                            desc(BedCount.create_date))
    if not force and not self._is_admin(session, user_id):
      # Fetch the IDs of ICUs that user is assigned to.
      user_icu_ids = session.query(
          icu_users.c.icu_id).filter(icu_users.c.user_id == user_id)
      # Find their regions.
      region_ids = session.query(ICU.region_id).filter(
          ICU.icu_id.in_(user_icu_ids.subquery()))
      # Fetch the IDs of the ICUs in these regions.
      region_icu_ids = session.query(ICU.icu_id).filter(
          ICU.region_id.in_(region_ids.subquery()))
      sub = sub.filter(BedCount.icu_id.in_(region_icu_ids.subquery()))

    if max_date:
      sub = sub.filter(BedCount.create_date < max_date)

    sub = sub.subquery()
    # Group by ICU ID drops bed counts except the most recent ones subject to
    # the date constraint above..
    latest = session.query(sub.c.rowid).group_by(sub.c.icu_id).subquery()
    # We want BedCount objects and hence to a final join.
    return session.query(BedCount).join(latest,
                                        latest.c.rowid == BedCount.rowid).all()

  # External client related methods.

  def get_access_key_hash(self, access_key: str) -> str:
    """Returns the hash of the access key."""
    return self.get_password_hash(access_key)

  def create_access_key(self) -> AccessKey:
    """Returns a new access key."""
    access_key = uuid.uuid1().hex
    return AccessKey(
        key=access_key, key_hash=self.get_access_key_hash(access_key))

  def add_external_client(
      self, admin_user_id: int,
      external_client: ExternalClient) -> Tuple[int, AccessKey]:
    """Adds a new external client and returns its access key.

    Args:
      admin_user_id: ID of an admin user.
      external_client: an ExternalClient object. access_key_hash field will be
        ignored.

    Returns:
      ID of the external client and the access key.
    """
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admins can add a new external client.")
      access_key = self.create_access_key()
      external_client.access_key_hash = access_key.key_hash
      session.add(external_client)
      session.commit()
      return external_client.external_client_id, access_key

  def update_external_client(self, admin_user_id: int, external_client_id: int,
                             values):
    """Updates an existing external client.

    Use reset_external_client_access_key() to change the access key.

    Args:
      admin_user_id: ID of an admin user.
      external_client_id: ID of the external client.
      values: a dict of external client fields to update.
    """
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admins can update an external client.")
      session.query(ExternalClient).filter(ExternalClient.external_client_id ==
                                           external_client_id).update(values)

  def get_external_client(self, external_client_id: int) -> ExternalClient:
    """Returns the external client with the specified ID."""
    return self._session().query(ExternalClient).filter(
        ExternalClient.external_client_id == external_client_id).one_or_none()

  def get_external_clients(self) -> Iterable[ExternalClient]:
    """Returns a list of external clients."""
    return self._session().query(ExternalClient).all()

  def auth_external_client(self, access_key: str) -> Optional[int]:
    """Authenticates an external client using the access key.

    Args:
      access_key: Access key of the external client.

    Returns:
      ID of the external client if there is a matching valid access key or None.
    """
    access_key_hash = self.get_access_key_hash(access_key)
    external_client = self._session().query(ExternalClient).filter(
        ExternalClient.access_key_hash == access_key_hash).one_or_none()
    if not external_client or not external_client.access_key_valid:
      return None
    return external_client.external_client_id

  def reset_external_client_access_key(
      self,
      admin_user_id: int,
      external_client_id: int,
      expiration_date: datetime = None) -> AccessKey:
    """Resets the access key of the external client and returns it."""
    with self.session_scope() as session:
      if not self._is_admin(session, admin_user_id):
        raise ValueError("Only admins can reset access keys.")
      external_client = session.query(ExternalClient).filter(
          ExternalClient.external_client_id == external_client_id).one()
      access_key = self.create_access_key()
      external_client.access_key_hash = access_key.key_hash
      external_client.expiration_date = expiration_date
      session.add(external_client)
      return access_key


def create_store_for_sqlite_db(cfg) -> Store:
  """Creates a store for the SQLite database with the specified path.

  Args:
   cfg: A config.Config instance

  Returns:
   A Store.
  """
  engine = create_engine("sqlite:///" + cfg.db.sqlite_path)
  return Store(engine, salt=cfg.DB_SALT)


def to_pandas(objs) -> pd.DataFrame:
  return pd.DataFrame([x.to_dict() for x in objs])
