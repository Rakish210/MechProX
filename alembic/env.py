import os
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL, make_url

from alembic import context
from mechpro.data import models  # noqa: F401
from mechpro.data.db import Base

config = context.config
target_metadata = Base.metadata


def configure_database_url() -> None:
    configured_url = os.environ.get("MECHPROX_DATABASE_URL")

    if configured_url:
        database_url = make_url(configured_url)
    else:
        configured_data_dir = os.environ.get("MECHPROX_DATA_DIR")
        data_dir = (
            Path(configured_data_dir).expanduser()
            if configured_data_dir
            else Path.home() / ".mechprox"
        )
        database_path = (data_dir / "mechprox.db").resolve()
        database_url = URL.create("sqlite", database=str(database_path))

    if (
        database_url.get_backend_name() == "sqlite"
        and database_url.database
        and database_url.database != ":memory:"
        and not database_url.database.startswith("file:")
    ):
        Path(database_url.database).expanduser().parent.mkdir(
            parents=True, exist_ok=True
        )

    rendered_url = database_url.render_as_string(hide_password=False)
    config.set_main_option("sqlalchemy.url", rendered_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    configure_database_url()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configure_database_url()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
