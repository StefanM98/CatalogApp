from datetime import datetime
import random
import string
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.types import TIMESTAMP, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

secret_key = ''.join(
    random.choice(string.ascii_uppercase + string.digits)
    for x in xrange(32))


def dump_datetime(value):
    # Deserialize datetime object into string form for JSON processing
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String, nullable=False)
    picture = Column(String, nullable=False)


class Catagory(Base):
    __tablename__ = 'catagory'
    id = Column(Integer, primary_key=True)
    name = Column(String(90), nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'created': dump_datetime(self.time_created),
            'updated': dump_datetime(self.time_updated)
            }


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(String(1000))
    image = Column(String, nullable=False)
    item_catagory = Column(String, ForeignKey('catagory.name'))
    catagory = relationship(Catagory)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image': self.image,
            'catagory': self.item_catagory,
            'created': dump_datetime(self.time_created),
            'updated': dump_datetime(self.time_updated)
        }


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
