import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column



# declarative base class
class Base(DeclarativeBase):
    pass

# mapped class
class Path(Base):
    __tablename__ = 'path'
    id = Column(Integer, primary_key=True)
    folder = Column(String(4096))

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(4096))


sql_uri = 'sqlite:///cwpl.sqlite'
sql_engine = sa.create_engine (sql_uri)

def init_db():
    Base.metadata.create_all(sql_engine)