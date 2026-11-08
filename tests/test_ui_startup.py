import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechpro.core.context import AppContext
from mechpro.data import models  # noqa: F401
from mechpro.data.db import Base
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import ProjectRepository
from mechpro.ui.main_window import MainWindow


def test_main_window_can_be_created_and_shown(tmp_path) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    engine = create_engine(f"sqlite:///{tmp_path / 'ui-test.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ProjectRepository(session_factory)
    parameter_repository = ParameterRegistryRepository(session_factory)
    window = MainWindow(AppContext(), repository, parameter_repository)
    window.show()
    app.processEvents()

    try:
        assert window.isVisible()
        assert window.nav.count() == 10
        assert window.stack.count() == 10
        assert window.section_title.text() == "Genel Bakış"
        assert window.projects.table.rowCount() == 0
        assert window.parameters.definition_table.rowCount() == 0
    finally:
        window.close()
