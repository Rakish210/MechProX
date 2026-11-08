import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.calculations.runner import CalculationRunner
from mechprox.core.context import AppContext
from mechprox.core.module_registry import ModuleHost, ModuleRegistry
from mechprox.data import models  # noqa: F401
from mechprox.data.catalogue_repository import CatalogueRepository
from mechprox.data.db import Base
from mechprox.data.parameter_registry_repository import ParameterRegistryRepository
from mechprox.data.project_repository import ProjectRepository
from mechprox.data.source_registry_repository import SourceRegistryRepository
from mechprox.engines.registry import create_default_calculation_engine_registry
from mechprox.modules import create_builtin_module_specs
from mechprox.ui.main_window import MainWindow


def test_main_window_is_composed_from_registered_module_pages(tmp_path) -> None:
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
        source_repository,
    )

    context = AppContext()
    context.services.register(ProjectRepository, repository)
    context.services.register(ParameterRegistryRepository, parameter_repository)
    context.services.register(CatalogueRepository, catalogue_repository)
    context.services.register(SourceRegistryRepository, source_repository)
    context.services.register(CalculationRunner, runner)

    registry = ModuleRegistry()
    for spec in create_builtin_module_specs():
        registry.register(spec)
    host = ModuleHost(registry, context)
    host.start()
    window = MainWindow(context, host)
    window.show()
    app.processEvents()

    try:
        assert window.isVisible()
        assert window.windowTitle().startswith("MechProX")
        assert window.brand_label.text() == "MechProX"
        assert window.nav.count() == 11
        assert window.stack.count() == 11
        assert window.section_title.text() == "Genel Bakış"

        pages = {
            spec.key: page for spec, page in zip(window._page_specs, window._pages, strict=True)
        }
        assert pages["workspace.projects"].table.rowCount() == 0
        assert pages["reference-data.parameters"].definition_table.rowCount() == 0
        assert pages["reference-data.sources"].source_table.rowCount() == 0
        assert pages["reference-data.sources"].standard_table.rowCount() == 0
        assert pages["engineering.calculations"].project_combo.count() == 0
        assert pages["reference-data.catalogue"].product_table.rowCount() == 0
        assert pages["engineering.model"].table.rowCount() == 0
        assert pages["commercial.takeoff"].bom_table.rowCount() == 0
        assert pages["commercial.takeoff"].boq_table.rowCount() == 0
    finally:
        window.close()
        host.stop()
