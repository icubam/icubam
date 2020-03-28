from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from backoffice.model.encoder import Serializer

Base = declarative_base()


class User(Base, Serializer):
  __tablename__ = 'user'
  id = Column(Integer, primary_key=True)
  name = Column('name', String(255))

  def to_json(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}