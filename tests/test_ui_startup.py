import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from typing import cast

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
from mechprox.ui.catalogue_page import CataloguePage
from mechprox.ui.commercial_page import CommercialPage
from mechprox.ui.engineering_data_page import EngineeringDataPage
from mechprox.ui.gas_demand_page import GasDemandPage
from mechprox.ui.main_window import MainWindow
from mechprox.ui.parameter_registry_page import ParameterRegistryPage
from mechprox.ui.project_page import ProjectPage
from mechprox.ui.source_registry_page import SourceRegistryPage


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
        projects_page = cast(ProjectPage, pages["workspace.projects"])
        parameter_page = cast(ParameterRegistryPage, pages["reference-data.parameters"])
        source_page = cast(SourceRegistryPage, pages["reference-data.sources"])
        calculations_page = cast(GasDemandPage, pages["engineering.calculations"])
        catalogue_page = cast(CataloguePage, pages["reference-data.catalogue"])
        engineering_page = cast(EngineeringDataPage, pages["engineering.model"])
        commercial_page = cast(CommercialPage, pages["commercial.takeoff"])

        assert projects_page.table.rowCount() == 0
        assert parameter_page.definition_table.rowCount() == 0
        assert source_page.source_table.rowCount() == 0
        assert source_page.standard_table.rowCount() == 0
        assert calculations_page.project_combo.count() == 0
        assert catalogue_page.product_table.rowCount() == 0
        assert engineering_page.table.rowCount() == 0
        assert commercial_page.bom_table.rowCount() == 0
        assert commercial_page.boq_table.rowCount() == 0
    finally:
        window.close()
        host.stop()
