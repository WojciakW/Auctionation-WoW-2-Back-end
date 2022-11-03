from sqlalchemy import ForeignKey, create_engine
from sqlalchemy import Column, String, BigInteger, Integer, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from local_settings import DB_URL

# initialize SQLAlchemy connection
database = create_engine(DB_URL)
Base = declarative_base()


class User(Base):
    """
    User data table.
    """
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)


class Item(Base):
    """
    WoW item data table.
    """
    __tablename__ = 'item_data'

    wow_item_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    name_slug = Column(String, nullable=True)
    class_ = Column(String)
    subclass = Column(String)
    slot = Column(String)
    quality = Column(String)
    icon_url = Column(Text)


class UserObservedItem(Base):
    """
    User-item many-to-many relation association table.
    """
    __tablename__ = 'user_observed_item'

    id = Column(BigInteger, primary_key=True)
    user = Column(BigInteger, ForeignKey('users.id'))
    item = Column(BigInteger, ForeignKey('item_data.wow_item_id'))


def setup_tables():
    """
    Used to create valid SQL tables.
    """
    Session = sessionmaker(database)
    session = Session()

    Base.metadata.create_all(database)

