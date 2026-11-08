import tempfile
from pathlib import Path

from mechpro.data import models  # noqa
from mechpro.data.db import Base, create_engine_sqlite


def test_db_create():
    d = Path(tempfile.mkdtemp())
    engine = create_engine_sqlite(d / "t.db")
    Base.metadata.create_all(engine)
    assert (d / "t.db").exists()
