"""Built-in modules that assemble existing workflows behind the module API."""

from mechprox.calculations.runner import CalculationRunner
from mechprox.core.context import AppContext
from mechprox.core.module_registry import ModuleManifest, ModulePageSpec, ModuleSpec
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


class _BuiltinModule:
    """Built-in pages currently own no background resources."""

    def configure(self, context: AppContext) -> None:
        return None

    def start(self, context: AppContext) -> None:
        return None

    def stop(self, context: AppContext) -> None:
        return None


def _spec(
    module_id: str,
    title: str,
    pages: tuple[ModulePageSpec, ...],
    *,
    dependencies: tuple[str, ...] = (),
) -> ModuleSpec:
    return ModuleSpec(
        manifest=ModuleManifest(
            module_id=module_id,
            title=title,
            version="1.0.0",
            dependencies=dependencies,
        ),
        factory=_BuiltinModule,
        pages=pages,
    )


def create_builtin_module_specs() -> tuple[ModuleSpec, ...]:
    """Return the initial module set; the host, not MainWindow, owns composition."""
    return (
        _spec(
            "workspace",
            "Project Workspace",
            (
                ModulePageSpec(
                    "dashboard",
                    "Genel Bakış",
                    lambda context: DashboardPage(
                        context.services.require(ProjectRepository)
                    ),
                    order=0,
                ),
                ModulePageSpec(
                    "projects",
                    "Projeler",
                    lambda context: ProjectPage(
                        context.services.require(ProjectRepository)
                    ),
                    order=10,
                ),
            ),
        ),
        _spec(
            "engineering",
            "Engineering Workspace",
            (
                ModulePageSpec(
                    "model",
                    "Mühendislik Verisi",
                    lambda context: EngineeringDataPage(
                        context.services.require(ProjectRepository),
                        context.services.require(CatalogueRepository),
                    ),
                    order=20,
                ),
                ModulePageSpec(
                    "calculations",
                    "Hesaplamalar",
                    lambda context: GasDemandPage(
                        context.services.require(ProjectRepository),
                        context.services.require(CalculationRunner),
                    ),
                    order=30,
                ),
            ),
            dependencies=("workspace",),
        ),
        _spec(
            "reference-data",
            "Engineering Reference Data",
            (
                ModulePageSpec(
                    "parameters",
                    "Parametre Kütüphanesi",
                    lambda context: ParameterRegistryPage(
                        context.services.require(ParameterRegistryRepository),
                        context.services.require(SourceRegistryRepository),
                    ),
                    order=40,
                ),
                ModulePageSpec(
                    "sources",
                    "Kaynak ve Standartlar",
                    lambda context: SourceRegistryPage(
                        context.services.require(SourceRegistryRepository)
                    ),
                    order=50,
                ),
                ModulePageSpec(
                    "catalogue",
                    "Ürün ve Poz Kütüphanesi",
                    lambda context: CataloguePage(
                        context.services.require(CatalogueRepository)
                    ),
                    order=60,
                ),
            ),
            dependencies=("workspace",),
        ),
        _spec(
            "commercial",
            "Commercial and Quantity",
            (
                ModulePageSpec(
                    "takeoff",
                    "BOM / BOQ",
                    lambda context: CommercialPage(
                        context.services.require(ProjectRepository)
                    ),
                    order=70,
                ),
            ),
            dependencies=("engineering", "reference-data"),
        ),
        _spec(
            "integrations",
            "External Integrations",
            (
                ModulePageSpec(
                    "cad-bim",
                    "CAD / BIM",
                    lambda context: ComingSoonPage(
                        "CAD / BIM",
                        "Gerçek AutoCAD ve Revit bağlantıları, ayrı adaptörler üzerinden "
                        "bu modüle eklenecek. Bu sayfa henüz entegrasyon içermez.",
                    ),
                    order=80,
                ),
            ),
            dependencies=("engineering",),
        ),
        _spec(
            "reporting",
            "Reporting",
            (
                ModulePageSpec(
                    "reports",
                    "Raporlar",
                    lambda context: ComingSoonPage(
                        "Raporlar",
                        "Teknik hesap raporları, metraj dökümleri ve proje teslim "
                        "çıktıları raporlama modülüne eklenecek.",
                    ),
                    order=90,
                ),
            ),
            dependencies=("engineering", "commercial"),
        ),
        _spec(
            "administration",
            "Administration",
            (
                ModulePageSpec(
                    "settings",
                    "Ayarlar",
                    lambda context: ComingSoonPage(
                        "Ayarlar",
                        "Yerel çalışma alanı, yedekleme ve entegrasyon ayarları.",
                    ),
                    order=100,
                ),
            ),
        ),
    )
