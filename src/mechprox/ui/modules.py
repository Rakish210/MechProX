from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from mechprox.calculations.runner import CalculationRunner
from mechprox.core.context import AppContext
from mechprox.core.module_registry import (
    ModuleManifest,
    ModuleRegistry,
    ModuleSpec,
    PlatformModule,
)
from mechprox.data.catalogue_repository import CatalogueRepository
from mechprox.data.parameter_registry_repository import ParameterRegistryRepository
from mechprox.data.project_repository import ProjectRepository
from mechprox.data.source_registry_repository import SourceRegistryRepository
from mechprox.ui.catalogue_page import CataloguePage
from mechprox.ui.commercial_page import CommercialPage
from mechprox.ui.engineering_data_page import EngineeringDataPage
from mechprox.ui.gas_demand_page import GasDemandPage
from mechprox.ui.parameter_registry_page import ParameterRegistryPage
from mechprox.ui.project_page import ComingSoonPage, DashboardPage, ProjectPage
from mechprox.ui.source_registry_page import SourceRegistryPage


class PageModule:
    """Adapter that gives an existing desktop page the platform module lifecycle."""

    def __init__(self, builder: Callable[[AppContext], QWidget]) -> None:
        self._builder = builder

    def configure(self, context: AppContext) -> None:
        return None

    def start(self, context: AppContext) -> None:
        return None

    def create_widget(self, context: AppContext) -> QWidget:
        return self._builder(context)

    def on_activated(self, context: AppContext, widget: QWidget) -> None:
        refresh = getattr(widget, "refresh", None)
        if callable(refresh):
            refresh()

    def stop(self, context: AppContext) -> None:
        return None


def _page_spec(
    module_id: str,
    title: str,
    order: int,
    builder: Callable[[AppContext], QWidget],
    *,
    description: str = "",
    dependencies: tuple[str, ...] = (),
    capabilities: tuple[str, ...] = (),
) -> ModuleSpec:
    manifest = ModuleManifest(
        module_id=module_id,
        title=title,
        version="1.0.0",
        dependencies=dependencies,
        capabilities=capabilities,
        description=description,
        navigation_order=order,
    )
    return ModuleSpec(manifest=manifest, factory=lambda: PageModule(builder))


def create_default_module_registry() -> ModuleRegistry:
    """Compose first-party workspaces through the same contract used by add-on modules."""
    registry = ModuleRegistry()
    registry.register(
        _page_spec(
            "dashboard",
            "Genel Bakış",
            10,
            lambda ctx: DashboardPage(ctx.services.require(ProjectRepository)),
            description="Project overview and workspace summary.",
            capabilities=("project.overview",),
        )
    )
    registry.register(
        _page_spec(
            "projects",
            "Projeler",
            20,
            lambda ctx: ProjectPage(ctx.services.require(ProjectRepository)),
            description="Project creation and lifecycle.",
            capabilities=("project.manage",),
        )
    )
    registry.register(
        _page_spec(
            "engineering",
            "Mühendislik Verisi",
            30,
            lambda ctx: EngineeringDataPage(
                ctx.services.require(ProjectRepository),
                ctx.services.require(CatalogueRepository),
            ),
            description="Common engineering data model editor.",
            dependencies=("projects",),
            capabilities=("engineering.data",),
        )
    )
    registry.register(
        _page_spec(
            "calculations",
            "Hesaplamalar",
            40,
            lambda ctx: GasDemandPage(
                ctx.services.require(ProjectRepository),
                ctx.services.require(CalculationRunner),
            ),
            description="Calculation workspaces. Discipline methods are registered separately.",
            dependencies=("engineering",),
            capabilities=("engineering.calculations",),
        )
    )
    registry.register(
        _page_spec(
            "parameters",
            "Parametre Kütüphanesi",
            50,
            lambda ctx: ParameterRegistryPage(
                ctx.services.require(ParameterRegistryRepository),
                ctx.services.require(SourceRegistryRepository),
            ),
            description="Versioned engineering parameters and approvals.",
            dependencies=("projects",),
            capabilities=("engineering.parameters",),
        )
    )
    registry.register(
        _page_spec(
            "sources",
            "Kaynak ve Standartlar",
            60,
            lambda ctx: SourceRegistryPage(ctx.services.require(SourceRegistryRepository)),
            description="Source documents, standards and clauses.",
            capabilities=("engineering.provenance",),
        )
    )
    registry.register(
        _page_spec(
            "library",
            "Ürün ve Poz Kütüphanesi",
            70,
            lambda ctx: CataloguePage(ctx.services.require(CatalogueRepository)),
            description="Physical products, BOQ positions and their mappings.",
            capabilities=("commercial.catalogue",),
        )
    )
    registry.register(
        _page_spec(
            "commercial",
            "BOM / BOQ",
            80,
            lambda ctx: CommercialPage(ctx.services.require(ProjectRepository)),
            description="Bill of materials and bill of quantities.",
            dependencies=("engineering", "library"),
            capabilities=("commercial.takeoff",),
        )
    )
    registry.register(
        _page_spec(
            "cad",
            "CAD / BIM",
            90,
            lambda ctx: ComingSoonPage(
                "CAD / BIM",
                "Native AutoCAD and Revit integrations are hosted here through versioned adapters. "
                "No drawing is edited by this placeholder workspace.",
            ),
            description="Native CAD and BIM adapters.",
            dependencies=("engineering",),
            capabilities=("cad.adapter-host", "bim.adapter-host"),
        )
    )
    registry.register(
        _page_spec(
            "reports",
            "Raporlar",
            100,
            lambda ctx: ComingSoonPage(
                "Raporlar",
                "Technical reports and commercial deliverables will use the common project model.",
            ),
            description="Traceable technical and commercial reports.",
            dependencies=("engineering",),
            capabilities=("reporting",),
        )
    )
    registry.register(
        _page_spec(
            "settings",
            "Ayarlar",
            110,
            lambda ctx: ComingSoonPage(
                "Ayarlar",
                "Local workspace, approved module packages, integrations and recovery settings.",
            ),
            description="Platform configuration and operations.",
            capabilities=("platform.settings",),
        )
    )
    return registry
