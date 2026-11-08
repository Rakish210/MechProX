from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass

def create_engine_sqlite(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False, future=True)

def create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
