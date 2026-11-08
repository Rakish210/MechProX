import os
import sys
from pathlib import Path

from alembic.config import Config
from PySide6.QtWidgets import QApplication

from alembic import command
from mechpro.core.config import ConfigManager
from mechpro.core.context import AppContext, configure_logging
from mechpro.data.db import create_engine_sqlite, create_session_factory
from mechpro.data.project_repository import ProjectRepository
from mechpro.ui.main_window import MainWindow


def _application_data_dir() -> Path:
    configured = os.environ.get("MECHPRO_DATA_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".mechpro"


def _initialize_database() -> ProjectRepository:
    data_dir = _application_data_dir()
    database_url = os.environ.get("MECHPRO_DATABASE_URL")
    if database_url:
        from sqlalchemy import create_engine

        engine = create_engine(database_url, future=True)
    else:
        engine = create_engine_sqlite(data_dir / "mechpro.db")

    project_root = Path(__file__).resolve().parents[2]
    alembic_path = project_root / "alembic.ini"
    if alembic_path.exists():
        migration_config = Config(str(alembic_path))
        command.upgrade(migration_config, "head")
    else:
        from mechpro.data import models  # noqa: F401
        from mechpro.data.db import Base

        Base.metadata.create_all(engine)

    return ProjectRepository(create_session_factory(engine))


def main() -> int:
    logger = configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("MechPro")
    app.setOrganizationName("MechPro")

    data_dir = _application_data_dir()
    config = ConfigManager(data_dir / "config.json")
    repository = _initialize_database()
    context = AppContext(config=config.data, logger=logger)
    window = MainWindow(context, repository)
    window.show()
    logger.info("MechPro desktop application started")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
