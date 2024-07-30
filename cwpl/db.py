import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


# declarative base class
class Base(DeclarativeBase):
    pass


# mapped class
class Path(Base):
    __tablename__ = "path"
    id = Column(Integer, primary_key=True, autoincrement=True)
    folder = Column(String(4096))

    def __repr__(self):
        return f"Path({self.id!r},'{self.folder!r}')"


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(4096))

    def __repr__(self):
        return f"User({self.id!r},'{self.name!r}')"


sql_uri = "sqlite:///cwpl.sqlite"
sql_engine = sa.create_engine(sql_uri)


def init_db():
    Base.metadata.create_all(sql_engine)


def get_all_paths():
    with Session(sql_engine) as session:
        return session.query(Path).all()


def get_all_users():
    with Session(sql_engine) as session:
        return session.query(User).all()


def add_user(name):
    with Session(sql_engine, expire_on_commit=False) as session:
        user = User(name=name)
        session.add(user)
        session.commit()
        return user


def add_path(folder):
    with Session(sql_engine, expire_on_commit=False) as session:
        path = Path(folder=folder)
        session.add(path)
        session.commit()
        return path


def delete_users(ids):
    with Session(sql_engine) as session:
        res = session.execute(sa.delete(User).where(User.id.in_(ids)))
        session.commit()
        return res.rowcount


def delete_users_by_name(name):
    with Session(sql_engine) as session:
        res = session.execute(sa.delete(User).where(User.name == name))
        session.commit()
        return res.rowcount


def delete_paths(ids):
    with Session(sql_engine) as session:
        res = session.execute(sa.delete(Path).where(Path.id.in_(ids)))
        session.commit()
        return res.rowcount


def delete_paths_by_folder(folder):
    with Session(sql_engine) as session:
        res = session.execute(sa.delete(Path).where(Path.folder == folder))
        session.commit()
        return res.rowcount


def update_user(id, new_name):
    with Session(sql_engine, expire_on_commit=False) as session:
        user = session.query(User).filter(User.id == id).first()
        if user is None:
            return None
        user.name = new_name
        session.commit()
        return user


def update_path(id, new_folder):
    with Session(sql_engine, expire_on_commit=False) as session:
        path = session.query(Path).filter(Path.id == id).first()
        if path is None:
            return None
        path.folder = new_folder
        session.commit()
        return path
