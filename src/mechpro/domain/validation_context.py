from dataclasses import dataclass, field
from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from mechpro.domain.base import IdentifiedModel, Quantity, QuantityValue, ReferenceValue, Revision
from mechpro.domain.calculations import CalculationRun
from mechpro.domain.commercial import PositionProductMapping, PositionReference, ProductReference
from mechpro.domain.engineering import EngineeringObjectRecord
from mechpro.domain.enums import ValidationSeverity
from mechpro.domain.model import EngineeringModel
from mechpro.domain.network import Network
from mechpro.domain.project import EngineeringSystem
from mechpro.domain.units import UnitService, UnitValidationError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    path: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass(slots=True)
class ValidationContext:
    model: EngineeringModel
    units: UnitService
    issues: list[ValidationIssue] = field(default_factory=list)
    entities: dict[UUID, IdentifiedModel] = field(default_factory=dict)
    object_by_id: dict[UUID, EngineeringObjectRecord] = field(default_factory=dict)
    network_by_id: dict[UUID, Network] = field(default_factory=dict)
    system_by_id: dict[UUID, EngineeringSystem] = field(default_factory=dict)
    product_by_id: dict[UUID, ProductReference] = field(default_factory=dict)
    position_by_id: dict[UUID, PositionReference] = field(default_factory=dict)
    mapping_by_id: dict[UUID, PositionProductMapping] = field(default_factory=dict)
    revision_by_id: dict[UUID, Revision] = field(default_factory=dict)
    run_by_id: dict[UUID, CalculationRun] = field(default_factory=dict)
    source_ids: set[UUID] = field(default_factory=set)
    geometry_ids: set[UUID] = field(default_factory=set)
    standard_ids: set[UUID] = field(default_factory=set)
    level_ids: set[UUID] = field(default_factory=set)
    discipline_codes: set[str] = field(default_factory=set)
    connector_owner: dict[UUID, UUID] = field(default_factory=dict)
    revision_target_ids: set[UUID] = field(default_factory=set)

    def __post_init__(self) -> None:
        collections = (
            (self.model.project,),
            self.model.buildings,
            self.model.levels,
            self.model.spaces,
            self.model.disciplines,
            self.model.systems,
            self.model.source_references,
            self.model.geometry_references,
            self.model.standard_references,
            self.model.revisions,
            self.model.approvals,
            self.model.objects,
            self.model.networks,
            self.model.connections,
            self.model.products,
            self.model.positions,
            self.model.position_product_mappings,
            self.model.bom_documents,
            self.model.boq_documents,
            self.model.calculation_runs,
            self.model.calculation_results,
        )
        for collection_index, collection in enumerate(collections):
            for item_index, entity in enumerate(collection):
                entity_id = entity.id
                if entity_id in self.entities:
                    previous = type(self.entities[entity_id]).__name__
                    self.add(
                        "duplicate_id",
                        f"ID is already used by {previous}.",
                        f"model[{collection_index}][{item_index}]",
                    )
                else:
                    self.entities[entity_id] = entity

        self.object_by_id = {item.id: item for item in self.model.objects}
        self.network_by_id = {item.id: item for item in self.model.networks}
        self.system_by_id = {item.id: item for item in self.model.systems}
        self.product_by_id = {item.id: item for item in self.model.products}
        self.position_by_id = {item.id: item for item in self.model.positions}
        self.mapping_by_id = {item.id: item for item in self.model.position_product_mappings}
        self.revision_by_id = {item.id: item for item in self.model.revisions}
        self.run_by_id = {item.id: item for item in self.model.calculation_runs}
        self.source_ids = {item.id for item in self.model.source_references}
        self.geometry_ids = {item.id for item in self.model.geometry_references}
        self.standard_ids = {item.id for item in self.model.standard_references}
        self.level_ids = {item.id for item in self.model.levels}
        self.discipline_codes = {item.code for item in self.model.disciplines}
        self.revision_target_ids = (
            {self.model.project.id}
            | {item.id for item in self.model.buildings}
            | {item.id for item in self.model.levels}
            | {item.id for item in self.model.spaces}
            | {item.id for item in self.model.systems}
            | {item.id for item in self.model.objects}
            | {item.id for item in self.model.networks}
            | {item.id for item in self.model.connections}
            | {item.id for item in self.model.products}
            | {item.id for item in self.model.positions}
            | {item.id for item in self.model.position_product_mappings}
            | {item.id for item in self.model.bom_documents}
            | {item.id for item in self.model.boq_documents}
            | {item.id for item in self.model.calculation_runs}
            | {item.id for item in self.model.calculation_results}
        )

    def add(
        self,
        code: str,
        message: str,
        path: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        self.issues.append(ValidationIssue(code, message, path, severity))

    def require(
        self,
        reference_id: UUID | None,
        expected_type: type[T],
        path: str,
        description: str,
    ) -> T | None:
        if reference_id is None:
            return None
        target = self.entities.get(reference_id)
        if target is None:
            self.add(
                "missing_reference",
                f"{description} references unknown ID '{reference_id}'.",
                path,
            )
            return None
        if not isinstance(target, expected_type):
            self.add(
                "wrong_reference_type",
                f"{description} points to an incompatible record.",
                path,
            )
            return None
        return target

    def validate_sources(self, source_ids: tuple[UUID, ...], path: str) -> None:
        for source_id in source_ids:
            if source_id not in self.source_ids:
                self.add(
                    "missing_source",
                    f"Source reference '{source_id}' does not exist.",
                    path,
                )

    def validate_unit(
        self,
        quantity: Quantity,
        path: str,
        expected_dimension: str | None = None,
    ) -> None:
        try:
            self.units.validate(quantity, expected_dimension=expected_dimension)
        except UnitValidationError as exc:
            self.add("invalid_unit", str(exc), path)

    def validate_unit_code(self, unit_code: str, path: str) -> None:
        self.validate_unit(Quantity(value=Decimal(1), unit_code=unit_code), path)

    def validate_object_sources(self, object_ids: tuple[UUID, ...], path: str) -> None:
        for object_id in object_ids:
            if object_id not in self.object_by_id:
                self.add(
                    "missing_source_object",
                    f"Source object '{object_id}' does not exist.",
                    path,
                )

    def validate_property_value(self, value: object, path: str) -> None:
        if isinstance(value, QuantityValue):
            self.validate_unit(value.quantity, path)
        elif isinstance(value, ReferenceValue) and value.target_id not in self.entities:
            self.add(
                "property_reference_missing",
                "Property references an unknown record.",
                f"{path}.target_id",
            )
