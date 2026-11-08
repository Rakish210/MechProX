from mechpro.domain.base import (
    ApprovalRecord,
    DomainModel,
    GeometryReference,
    Revision,
    SourceReference,
    StandardReference,
)
from mechpro.domain.calculations import CalculationResult, CalculationRun
from mechpro.domain.commercial import (
    BOMDocument,
    BOQDocument,
    PositionProductMapping,
    PositionReference,
    ProductReference,
)
from mechpro.domain.engineering import EngineeringObjectRecord
from mechpro.domain.network import Connection, Network
from mechpro.domain.project import (
    Building,
    Discipline,
    EngineeringSystem,
    Level,
    Project,
    Space,
)


class EngineeringModel(DomainModel):
    """Versioned model aggregate for a single engineering project revision."""

    schema_version: str = "1.0"
    project: Project
    buildings: tuple[Building, ...] = ()
    levels: tuple[Level, ...] = ()
    spaces: tuple[Space, ...] = ()
    disciplines: tuple[Discipline, ...] = ()
    systems: tuple[EngineeringSystem, ...] = ()
    source_references: tuple[SourceReference, ...] = ()
    geometry_references: tuple[GeometryReference, ...] = ()
    standard_references: tuple[StandardReference, ...] = ()
    revisions: tuple[Revision, ...] = ()
    approvals: tuple[ApprovalRecord, ...] = ()
    objects: tuple[EngineeringObjectRecord, ...] = ()
    networks: tuple[Network, ...] = ()
    connections: tuple[Connection, ...] = ()
    products: tuple[ProductReference, ...] = ()
    positions: tuple[PositionReference, ...] = ()
    position_product_mappings: tuple[PositionProductMapping, ...] = ()
    bom_documents: tuple[BOMDocument, ...] = ()
    boq_documents: tuple[BOQDocument, ...] = ()
    calculation_runs: tuple[CalculationRun, ...] = ()
    calculation_results: tuple[CalculationResult, ...] = ()
