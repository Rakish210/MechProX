import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.calculations.runner import CalculationRunner
from mechprox.core.context import AppContext
from mechprox.data import models  # noqa: F401
from mechprox.data.catalogue_repository import CatalogueRepository
from mechprox.data.db import Base
from mechprox.data.parameter_registry_repository import ParameterRegistryRepository
from mechprox.data.project_repository import ProjectRepository
from mechprox.data.source_registry_repository import SourceRegistryRepository
from mechprox.engines.registry import create_default_calculation_engine_registry
from mechprox.ui.main_window import MainWindow


def test_main_window_can_be_created_and_shown(tmp_path) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    engine = create_engine(f"sqlite:///{tmp_path / 'ui-test.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ProjectRepository(session_factory)
    parameter_repository = ParameterRegistryRepository(session_factory)
    catalogue_repository = CatalogueRepository(session_factory)
    source_repository = SourceRegistryRepository(session_factory)
    runner = CalculationRunner(
        create_default_calculation_engine_registry(),
        parameter_repository,
    )
    window = MainWindow(
        AppContext(), repository, parameter_repository, runner, catalogue_repository,
        source_repository,
    )
    window.show()
    app.processEvents()

    try:
        assert window.isVisible()
        assert window.windowTitle().startswith("MechProX")
        assert window.brand_label.text() == "MechProX"
        assert window.nav.count() == 11
        assert window.stack.count() == 11
        assert window.section_title.text() == "Genel Bakış"
        assert window.projects.table.rowCount() == 0
        assert window.parameters.definition_table.rowCount() == 0
        assert window.sources.source_table.rowCount() == 0
        assert window.sources.standard_table.rowCount() == 0
        assert window.calculations.project_combo.count() == 0
        assert window.catalogue.product_table.rowCount() == 0
        assert window.catalogue.position_table.rowCount() == 0
        assert window.engineering_data.table.rowCount() == 0
        assert window.commercial.bom_table.rowCount() == 0
        assert window.commercial.boq_table.rowCount() == 0
    finally:
        window.close()
