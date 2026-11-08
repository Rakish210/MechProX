import os
import sys
from pathlib import Path

from alembic.config import Config
from PySide6.QtWidgets import QApplication

from alembic import command
from mechpro.calculations.runner import CalculationRunner
from mechpro.core.config import ConfigManager
from mechpro.core.context import AppContext, configure_logging
from mechpro.data.db import create_engine_sqlite, create_session_factory
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import ProjectRepository
from mechpro.engines.registry import create_default_calculation_engine_registry
from mechpro.ui.main_window import MainWindow


def _application_data_dir() -> Path:
    configured = os.environ.get("MECHPROX_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".mechprox"


def _initialize_database() -> tuple[ProjectRepository, ParameterRegistryRepository]:
    data_dir = _application_data_dir()
    database_url = os.environ.get("MECHPROX_DATABASE_URL")
    if database_url:
        from sqlalchemy import create_engine

        engine = create_engine(database_url, future=True)
    else:
        engine = create_engine_sqlite(data_dir / "mechprox.db")

    project_root = Path(__file__).resolve().parents[2]
    alembic_path = project_root / "alembic.ini"
    if alembic_path.exists():
        migration_config = Config(str(alembic_path))
        command.upgrade(migration_config, "head")
    else:
        from mechpro.data import models  # noqa: F401
        from mechpro.data.db import Base

        Base.metadata.create_all(engine)

    session_factory = create_session_factory(engine)
    return (
        ProjectRepository(session_factory),
        ParameterRegistryRepository(session_factory),
    )


def main() -> int:
    logger = configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("MechProX")
    app.setOrganizationName("MechProX")

    data_dir = _application_data_dir()
    config = ConfigManager(data_dir / "config.json")
    project_repository, parameter_repository = _initialize_database()
    context = AppContext(config=config.data, logger=logger)
    calculation_runner = CalculationRunner(
        create_default_calculation_engine_registry(),
        parameter_repository,
    )
    window = MainWindow(
        context,
        project_repository,
        parameter_repository,
        calculation_runner,
    )
    window.show()
    logger.info("MechProX desktop application started")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
