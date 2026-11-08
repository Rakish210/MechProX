from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from mechprox.domain.base import (
    EngineeringProperty,
    IdentifiedModel,
    PropertyValue,
    SourceReference,
    StandardReference,
)
from mechprox.domain.engineering import EngineeringObjectRecord
from mechprox.domain.enums import CalculationPurpose, CalculationState
from mechprox.domain.parameters import ParameterRevision


class ParameterSnapshot(IdentifiedModel):
    parameter_code: str
    value: PropertyValue
    parameter_revision: str
    source_reference_ids: tuple[UUID, ...] = ()
    revision_snapshot: ParameterRevision | None = None


class CalculationInputSnapshot(IdentifiedModel):
    engineering_object_id: UUID
    object_revision_id: UUID
    object_snapshot: EngineeringObjectRecord | None = None
    property_snapshots: tuple[EngineeringProperty, ...] = ()
    parameter_snapshots: tuple[ParameterSnapshot, ...] = ()
    source_reference_ids: tuple[UUID, ...] = ()
    snapshot_hash: str = Field(min_length=1)


class CalculationRun(IdentifiedModel):
    project_id: UUID
    method_code: str
    method_revision: str
    engine_name: str
    engine_version: str
    purpose: CalculationPurpose = CalculationPurpose.ENGINEERING
    state: CalculationState = CalculationState.PREPARED
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    input_snapshots: tuple[CalculationInputSnapshot, ...]
    standard_reference_ids: tuple[UUID, ...] = ()
    standard_snapshots: tuple[StandardReference, ...] = ()
    source_reference_snapshots: tuple[SourceReference, ...] = ()
    input_hash: str = Field(min_length=1)
    output_hash: str | None = None
    warnings: tuple[str, ...] = ()
    error_message: str | None = None


class CalculationResult(IdentifiedModel):
    calculation_run_id: UUID
    result_code: str
    label: str
    value: PropertyValue
    source_object_ids: tuple[UUID, ...] = ()
    source_parameter_codes: tuple[str, ...] = ()
    standard_reference_ids: tuple[UUID, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
