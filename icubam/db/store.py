"""Data store for ICUBAM."""
from typing import Dict, Any

from absl import logging
import enum
import pandas as pd
from contextlib import contextmanager
import dataclasses
from datetime import datetime
import hashlib
from sqlalchemy import create_engine, desc, func
from sqlalchemy import Column, Table
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean, Enum, Float, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import text
from typing import Iterable, Optional, Tuple
import uuid


class Base(object):
  """Base with helper methods."""

  @classmethod
  def get_column_names(cls, include_relationships=True):
    """Returns the columns of the table."""
    result = list(cls.__mapper__.columns.keys())
    if include_relationships:
      result.extend(cls.__mapper__.relationships.keys())
    return result

  def to_dict(self, max_depth=1, include_relationships=True) -> dict:
    """Turns a Base instance into a dictionary.

    Args:
     max_depth: the maximum recursion depth.
    """
    columns = self.get_column_names(include_relationships=include_relationships)

    result = {}
    for col in columns:
      value = getattr(self, col)
      if isinstance(value, Base):
        if max_depth > 0:
          result[col] = value.to_dict(max_depth - 1)
      elif isinstance(value, list):
        result[col] = []
        for elem in value:
          if isinstance(elem, Base):
            if max_depth > 0:
              result[col].append(elem.to_dict(max_depth - 1))
          else:
            result[col].append(elem)
      else:
        result[col] = value

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

# Regions that external clients can access.
external_client_regions = Table(
    "external_client_regions", Base.metadata,
    Column(
        "external_client_id",
        ForeignKey("external_clients.external_client_id"),
        primary_key=True),
    Column("region_id", ForeignKey("regions.region_id"), primary_key=True))


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


class AccessTypes(enum.Enum):
  MAP = 1
  STATS = 2
  UPLOAD = 3
  ALL = 4


class ExternalClient(Base):
  "Represents an external client that can access ICUBAM data." ""
  __tablename__ = "external_clients"

  external_client_id = Column(Integer, primary_key=True)
  name = Column(String)
  email = Column(String)
  telephone = Column(String)
  # Strong hash of the access key. It should be unique.
  access_key_hash = Column(String, unique=True)
  # This is to be unused at some point.
  access_key = Column(String, unique=True)
  # If set, denotes the date that the access key expires.
  expiration_date = Column(DateTime)
  is_active = Column(Boolean, default=True, server_default=text("1"))
  # Type of access: map, stats, both
  access_type = Column(Enum(AccessTypes))

  create_date = Column(DateTime, default=func.now())
  last_modified = Column(DateTime, default=func.now(), onupdate=func.now())

  # Regions that an external client can access.
  regions = relationship("Region", secondary=external_client_regions)

  @property
  def access_key_valid(self):
    """Returns true if the access key is valid."""
    return (
      (self.expiration_date is None or self.expiration_date > datetime.now())
      and self.is_active)

@dataclasses.dataclass
class AccessKey(object):
  """Access key together with its hash."""
  key: str
  key_hash: str


class StoreFactory:
  """Factory for creating stores."""

  def __init__(self, engine, salt=""):
    if salt is None:
      logging.warning("DB_SALT is not defined. Falling back to default")
      salt = ""

    Base.metadata.create_all(engine)
    self._session_factory = sessionmaker(bind=engine)
    self._salt = salt.encode()

  def create(self):
    return Store(self._session_factory(), self._salt)


class Store(object):
  """Provides high level access to the data store."""

  def __init__(self, session, salt):
    """Creates a store.

    The session will be closed when the store is destructed.

    Args:
      session: a DB session.
      salt: salt used when creating hashes.
    """
    self._session = session
    self._salt = salt

  @contextmanager
  def _commit_or_rollback(self):
    """Provide a transactional scope around a series of operations."""
    try:
      yield
      self._session.commit()
    except:
      self._session.rollback()
      raise

  def is_admin(self, user_id: int) -> bool:
    """Returns true if the user with the specified ID is an admin."""
    user = self.get_user(user_id)
    return bool(user and user.is_admin)

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

    if self.is_admin(admin_user_id):
      self._session.add(icu)
      self._session.commit()
      return icu.icu_id

    rids = set([i.region_id for i in self.get_managed_icus(admin_user_id)])
    if icu.region_id not in rids:
      raise ValueError("New ICUs can only be created in the manger's region.")

    self._session.add(icu)
    self._session.commit()

    # Make sure this manager manages this ICU.
    self.assign_user_as_icu_manager(
      admin_user_id, admin_user_id, icu.icu_id, force=True)

    return icu.icu_id

  def get_icu(self, icu_id: int) -> Optional[ICU]:
    """Returns the ICU with the specified ID."""
    return self._session.query(ICU).filter(ICU.icu_id == icu_id).one_or_none()

  def get_icus(self) -> Iterable[ICU]:
    """Returns all users, e.g. sync. Do not use in user facing code."""
    return self._session.query(ICU).all()

  def update_icu(self, manager_user_id: int, icu_id: int, values):
    """Updates an existing ICU.

    Args:
      manager_user_id: ID of the user that manages the ICU.
      icu_id: ID of the ICU.
      values: a dict of ICU fields to update.
    """
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("User does not own the ICU.")
    with self._commit_or_rollback():
      self._session.query(ICU).filter(ICU.icu_id == icu_id).update(values)

  def manages_icu(self, user_id: int, icu_id: int) -> bool:
    """Returns true if the user manages the ICU with the specified ID."""
    if self.is_admin(user_id):
      return True
    return self._session.query(icu_managers).filter(
        icu_managers.c.user_id == user_id).filter(
            icu_managers.c.icu_id == icu_id).count() == 1

  def enable_icu(self, manager_user_id: int, icu_id: int, is_active=True):
    """Enables the ICU with the specified ID."""
    self.update_icu(manager_user_id, icu_id, {"is_active": is_active})

  def disable_icu(self, manager_user_id: int, icu_id: int):
    """Disables the ICU with the specified ID."""
    self.enable_icu(manager_user_id, icu_id, False)

  def assign_user_as_icu_manager(self, admin_user_id: int, manager_user_id: int,
                                 icu_id: int, force: bool = False):
    """Assigns the specified user as a manager of an ICU.

    The force parameter is used to bypass the admin condition in specific
    situations such as when a manager want to create an ICU.
    """
    if not force and not self.is_admin(admin_user_id):
      raise ValueError("Only admin users can assign managers to ICUs.")
    with self._commit_or_rollback():
      self._session.execute(icu_managers.insert().values(
          user_id=manager_user_id, icu_id=icu_id))

  def remove_manager_user_from_icu(self, admin_user_id: int,
                                   manager_user_id: int, icu_id: int):
    """Removed the manager user from an ICU."""
    if not self.is_admin(admin_user_id):
      raise ValueError("Only admin users can remove managers from ICUs.")
    with self._commit_or_rollback():
      self._session.execute(icu_managers.delete().where(
          icu_managers.c.user_id == manager_user_id).where(
              icu_managers.c.icu_id == icu_id))

  def get_managed_icus(self, manager_user_id: int) -> Iterable[ICU]:
    """Returns the list of ICUs managed by the user."""
    # Admins can manage all ICUs.
    if self.is_admin(manager_user_id):
      return self._session.query(ICU).all()
    user = self.get_user(manager_user_id)
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
    self._session.add(user)
    self._session.commit()
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

  def get_user(self, user_id: int) -> Optional[User]:
    """Returns the user with the specified ID."""
    return self._session.query(User).filter(
        User.user_id == user_id).one_or_none()

  def get_users(self) -> Iterable[User]:
    """Returns all users, e.g. sync. Do not use in user facing code."""
    return self._session.query(User).all()

  def get_admins(self) -> Iterable[User]:
    """Returns all admins, e.g. sync. Do not use in user facing code."""
    return self._session.query(User).filter(User.is_admin).all()

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
    with self._commit_or_rollback():
      self._session.query(User).filter(User.user_id == user_id).update(values)

  def assign_user_to_icu(self, manager_user_id: int, user_id: int, icu_id: int):
    """Assigns the specified user to an ICU."""
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("Only managers can assign users to a ICU.")
    with self._commit_or_rollback():
      self._session.execute(icu_users.insert().values(
          user_id=user_id, icu_id=icu_id))

  def remove_user_from_icu(self, manager_user_id: int, user_id: int,
                           icu_id: int):
    """Removes an existing assignment of user to an ICU."""
    if not self.manages_icu(manager_user_id, icu_id):
      raise ValueError("Only managers can remove users from an ICU.")
    with self._commit_or_rollback():
      self._session.execute(icu_users.delete().where(
          icu_users.c.user_id == user_id).where(icu_users.c.icu_id == icu_id))

  def enable_user(self, manager_user_id: int, user_id: int, is_active=True):
    """Enables the user with the specified ID."""
    self.update_user(manager_user_id, user_id, {"is_active": is_active})

  def disable_user(self, manager_user_id: int, user_id: int):
    """Disables the user with the specified ID."""
    self.enable_user(manager_user_id, user_id, False)

  def manages_user(self, manager_user_id: int, user_id: int) -> bool:
    """Returns true if the manager user can manage the user."""
    if self.is_admin(manager_user_id) or manager_user_id == user_id:
      return True

    # TODO(olivier): use a sql query instead.
    user = self.get_user(user_id)
    if user is None:
      return False

    managed_icu_ids = set(
      [i.icu_id for i in self.get_managed_icus(manager_user_id)])
    user_icu_ids = set([i.icu_id for i in user.icus])
    return len(managed_icu_ids.intersection(user_icu_ids)) > 0

  def get_managed_users(self, manager_user_id: int) -> Iterable[User]:
    """Returns the list of users managed by the manager user."""
    icus = self.get_managed_icus(manager_user_id)
    if not icus:
      return []
    icu_ids = [icu.icu_id for icu in icus]
    return self._session.query(User).join(icu_users).filter(
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
    return self._session.query(User.user_id).filter(User.email == email).filter(
        User.password_hash == self.get_password_hash(password)).scalar()

  def get_user_by_email(self, email: str) -> int:
    return self._session.query(User.user_id).filter(
        User.email == email).scalar()

  def auth_user_by_token(self, token: str) -> int:
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
      raise ValueError("ID of a new region should not be set.")
    if not self.is_admin(admin_user_id):
      raise ValueError("Only admins can add a new region.")
    self._session.add(region)
    self._session.commit()
    return region.region_id

  def get_region(self, region_id: int) -> Optional[Region]:
    """Returns the region with the specified ID."""
    return self._session.query(Region).filter(
        Region.region_id == region_id).one_or_none()

  def get_regions(self) -> Iterable[Region]:
    """Returns the list of regions."""
    return self._session.query(Region).all()

  def update_region(self, admin_user_id: int, region_id: int, values):
    """Updates an existing region.

    Args:
      admin_user_id: ID of the admin user.
      region_id: ID of the region.
      values: a dict of Region fields to update.
    """
    if not self.is_admin(admin_user_id):
      raise ValueError("Only admins can update a region.")
    with self._commit_or_rollback():
      self._session.query(Region).filter(
          Region.region_id == region_id).update(values)

  def get_icus_in_region(self, region_id: int) -> Iterable[ICU]:
    """Returns the ICUs in the region with the specified ID."""
    return self._session.query(Region).filter(
        Region.region_id == region_id).one().icus

  # Bed count related methods.

  def get_bed_count_for_icu(self, icu_id: int) -> Optional[BedCount]:
    return self._session.query(BedCount).filter(
        BedCount.icu_id == icu_id).order_by(desc(BedCount.create_date)).first()

  def update_bed_count_for_icu(self,
                               user_id: int,
                               bed_count: BedCount,
                               force=False):
    """Updates the latest bed count for the specified ICU."""
    if not self.can_edit_bed_count(user_id, bed_count.icu_id) and not force:
      raise ValueError("User cannot edit bed count for the ICU.")
    self._session.add(bed_count)
    self._session.commit()

  def can_edit_bed_count(self, user_id: int, icu_id: int) -> bool:
    """Returns true if the user can edit the bed count for the specified ICU."""
    if self.is_admin(user_id):
      return True
    return self._session.query(icu_users).filter(
        icu_users.c.user_id == user_id).filter(
            icu_users.c.icu_id == icu_id).count() == 1

  def _get_latest_bed_counts_for_icus(self,
                                      icu_ids,
                                      max_date: datetime = None,
                                     ) -> Iterable[BedCount]:
    """Returns the latest bed counts of the ICUs.

    Args:
      icu_ids: subquery of ICU IDs or None for all ICUs.
      max_date: Restricts the time of the bed counts to this date.

    Returns:
      a list of BedCounts.
    """
    session = self._session
    # Bed counts in reverse chronological order.
    sub = session.query(BedCount.rowid, BedCount.icu_id,
                    BedCount.create_date).order_by(
                      desc(BedCount.create_date)
                    ).join(ICU, BedCount.icu_id == ICU.icu_id).filter(
                      ICU.is_active == True
                    )

    if icu_ids is not None:
      sub = sub.filter(BedCount.icu_id.in_(icu_ids))

    if max_date:
      sub = sub.filter(BedCount.create_date < max_date)

    sub = sub.subquery()
    # Group by ICU ID drops bed counts except the most recent ones subject to
    # the date constraint above..
    latest = session.query(sub.c.rowid).group_by(sub.c.icu_id).subquery()
    # We want BedCount objects and hence to a final join.
    return session.query(BedCount).join(latest,
                                        latest.c.rowid == BedCount.rowid).all()

  def _get_bed_counts_for_icus(self,
                               icu_ids,
                               latest=False,
                               max_date: datetime = None) -> Iterable[BedCount]:
    """Returns the (latest) bed counts of the ICUs.

    Args:
      icu_ids: subquery of ICU IDs or None for all ICUs.
      latest: if true, then only the latest bed counts satisfying the conditions
        will be returned.
      max_date: Restricts the time of the bed counts to this date.

    Returns:
      a list of BedCounts.
    """
    if latest:
      return self._get_latest_bed_counts_for_icus(icu_ids, max_date=max_date)
    # Bed counts in reverse chronological order.
    query = self._session.query(BedCount).order_by(desc(BedCount.create_date))
    if icu_ids is not None:
      query = query.filter(BedCount.icu_id.in_(icu_ids))

    if max_date:
      query = query.filter(BedCount.create_date < max_date)
    query = query.filter(ICU.is_active == True)
    return query.all()

  def get_latest_bed_counts(self, icu_ids=None, **kargs) -> Iterable[BedCount]:
    """Returns the latest bed counts.

    kargs are used for additional filtering, e.g. max_date.

    Args:
      icu_ids: a list or subquery of ICU IDs or None for all ICUs.

    Returns:
      a list of BedCounts, one for each ICU.
    """
    return self.get_bed_counts(icu_ids, latest=True, **kargs)

  def get_bed_counts(self,
                     icu_ids=None,
                     latest=False,
                     **kargs) -> Iterable[BedCount]:
    """Returns the (latest) bed counts.

    kargs are used for additional filtering, e.g. max_date.

    Args:
      icu_ids: a list or subquery of ICU IDs or None for all ICUs.
      latest: if true, then only the latest bed counts satisfying the conditions
        will be returned.

    Returns:
      a list of BedCounts, one or more for each ICU.
    """
    return self._get_bed_counts_for_icus(icu_ids, latest=latest, **kargs)

  def get_visible_bed_counts_for_user(self,
                                      user_id: int,
                                      force=False,
                                      **kargs) -> Iterable[BedCount]:
    """Returns the latest bed counts of ICS that are visible to the user.

    Admin users can view all ICUs. For other users, only ICUs that are in the
    same regions as the ICUs that they are assigned to will be visible.

    kargs are passed to get_latest_bed_counts_for_icus() method for additional
    filtering, e.g. max_date.
    """
    # TODO: handle user=None here (#180)
    user = self.get_user(user_id)
    if force or user.is_admin:
      return self._get_bed_counts_for_icus(None, latest=True, **kargs)
    else:
      icu_ids = set()
      icu_ids.update([icu.icu_id for icu in user.icus])
      icu_ids.update([icu.icu_id for icu in user.managed_icus])
    return self.get_visible_bed_counts_in_same_region(icu_ids, **kargs)

  def get_visible_bed_counts_in_same_region(self, icu_ids: Iterable[int],
                                            **kargs) -> Iterable[BedCount]:
    """Returns the latest bed counts in the regions of the specified ICUs.

    kargs are passed to get_latest_bed_counts_for_icus() method for additional
    filtering, e.g. max_date.

    Args:
      icu_ids: a list of ICU IDs.

    Returns:
      a list of BedCounts for the ICUs that are in the same regions as the input
      ICUs.
    """
    # Find the regions of the ICUs.
    session = self._session
    region_ids = session.query(ICU.region_id).filter(ICU.icu_id.in_(icu_ids))
    # Fetch the IDs of the ICUs in these regions.
    region_icu_ids = session.query(ICU.icu_id).filter(
      ICU.region_id.in_(region_ids.subquery())
    ).filter(ICU.is_active == True)
    return self._get_bed_counts_for_icus(
        region_icu_ids.subquery(), latest=True, **kargs)

  def get_bed_counts_for_external_client(self,
                                         external_client_id: int,
                                         latest=False,
                                         **kargs) -> Iterable[BedCount]:
    """Returns the latest bed counts for the external client.

    kargs are passed to get_latest_bed_counts_for_icus() method for additional
    filtering, e.g. max_date.

    Args:
      external_client_id: ID of the external client.
      latest: if true, then only the latest bed counts satisfying the conditions
        will be returned.

    Returns:
      a list of BedCounts.
    """
    # Find the regions of the external client.
    session = self._session
    region_ids = session.query(external_client_regions.c.region_id).filter(
        external_client_regions.c.external_client_id == external_client_id)
    region_icu_ids = session.query(ICU.icu_id).filter(
        ICU.region_id.in_(region_ids.subquery()))
    return self._get_bed_counts_for_icus(
        region_icu_ids.subquery(), latest=latest, **kargs)

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
    if not self.is_admin(admin_user_id):
      raise ValueError("Only admins can add a new external client.")
    access_key = self.create_access_key()
    external_client.access_key_hash = access_key.key_hash
    # TODO(olivier): remove this later.
    external_client.access_key = access_key.key
    self._session.add(external_client)
    self._session.commit()
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
    if not self.is_admin(admin_user_id):
      raise ValueError("Only admins can update an external client.")
    with self._commit_or_rollback():
      self._session.query(ExternalClient).filter(
          ExternalClient.external_client_id == external_client_id).update(
              values)

  def get_external_client_by_email(self, email: str) -> ExternalClient:
    """Returns the external client with the specified ID."""
    return self._session.query(ExternalClient).filter(
        ExternalClient.email == email).one_or_none()

  def get_external_client(self, external_client_id: int) -> ExternalClient:
    """Returns the external client with the specified ID."""
    return self._session.query(ExternalClient).filter(
        ExternalClient.external_client_id == external_client_id).one_or_none()

  def get_external_clients(self) -> Iterable[ExternalClient]:
    """Returns a list of external clients."""
    return self._session.query(ExternalClient).all()

  def auth_external_client(self, access_key: str) -> Optional[int]:
    """Authenticates an external client using the access key.

    Args:
      access_key: Access key of the external client.

    Returns:
      ID of the external client if there is a matching valid access key or None.
    """
    access_key_hash = self.get_access_key_hash(access_key)
    external_client = self._session.query(ExternalClient).filter(
        ExternalClient.access_key_hash == access_key_hash).one_or_none()
    if not external_client or not external_client.access_key_valid:
      return None
    return external_client

  def reset_external_client_access_key(
      self,
      admin_user_id: int,
      external_client_id: int,
      expiration_date: datetime = None) -> AccessKey:
    """Resets the access key of the external client and returns it."""
    if not self.is_admin(admin_user_id):
      raise ValueError("Only admins can reset access keys.")
    with self._commit_or_rollback():
      external_client = self._session.query(ExternalClient).filter(
          ExternalClient.external_client_id == external_client_id).one()
      access_key = self.create_access_key()
      external_client.access_key_hash = access_key.key_hash
      external_client.expiration_date = expiration_date
      self._session.add(external_client)
      return access_key

  def assign_external_client_to_region(self, admin_user_id: int,
                                       external_client_id: int, region_id: int):
    """Assigns the external client to a region."""
    if not self.is_admin(admin_user_id):
      raise ValueError(
          "Only admin users can assign external clients to regions.")
    with self._commit_or_rollback():
      self._session.execute(external_client_regions.insert().values(
          external_client_id=external_client_id, region_id=region_id))

  def remove_external_client_from_region(self, admin_user_id: int,
                                         external_client_id: int,
                                         region_id: int):
    """Removes the external client from a region."""
    if not self.is_admin(admin_user_id):
      raise ValueError(
          "Only admin users can assign external clients to regions.")
    with self._commit_or_rollback():
      self._session.execute(external_client_regions.delete().where(
          external_client_regions.c.external_client_id == external_client_id
      ).where(external_client_regions.c.region_id == region_id))


def create_store_factory_for_sqlite_db(cfg) -> Store:
  """Creates a store for the SQLite database with the specified path.

  Args:
   cfg: A config.Config instance

  Returns:
   A Store.
  """
  engine = create_engine("sqlite:///" + cfg.db.sqlite_path)
  return StoreFactory(engine, salt=cfg.DB_SALT)


def to_pandas(objs, max_depth=1):
  return pd.json_normalize([obj.to_dict(max_depth=max_depth) for obj in objs], sep="_")
