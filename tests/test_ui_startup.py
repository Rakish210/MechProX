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


def test_main_window_is_composed_from_registered_modules(tmp_path) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    engine = create_engine(f"sqlite:///{tmp_path / 'ui-test.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    project_repository = ProjectRepository(session_factory)
    parameter_repository = ParameterRegistryRepository(session_factory)
    catalogue_repository = CatalogueRepository(session_factory)
    source_repository = SourceRegistryRepository(session_factory)
    calculation_runner = CalculationRunner(
        create_default_calculation_engine_registry(),
        parameter_repository,
        source_repository,
    )

    context = AppContext()
    context.services.register(ProjectRepository, project_repository)
    context.services.register(ParameterRegistryRepository, parameter_repository)
    context.services.register(CatalogueRepository, catalogue_repository)
    context.services.register(SourceRegistryRepository, source_repository)
    context.services.register(CalculationRunner, calculation_runner)

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
        assert host.started_module_ids == (
            "workspace",
            "engineering",
            "reference-data",
            "commercial",
            "integrations",
            "reporting",
            "administration",
        )
        assert window.nav.item(0).text() == "Genel Bakış"
        assert window.nav.item(1).text() == "Projeler"
        assert window.nav.item(2).text() == "Mühendislik Verisi"
        assert window.nav.item(7).text() == "BOM / BOQ"

        window.nav.setCurrentRow(2)
        app.processEvents()
        assert window.section_title.text() == "Mühendislik Verisi"
        assert window.status_label.text() == "Yerel veritabanı"

        window.nav.setCurrentRow(0)
        app.processEvents()
        assert window.stack.currentIndex() == 0
    finally:
        window.close()
        host.stop()
