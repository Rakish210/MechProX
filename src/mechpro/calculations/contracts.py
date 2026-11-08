from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from mechpro.domain.base import PropertyValue, StandardReference
from mechpro.domain.calculations import CalculationResult, CalculationRun
from mechpro.domain.engineering import EngineeringObjectRecord
from mechpro.domain.enums import CalculationPurpose
from mechpro.domain.model import EngineeringModel
from mechpro.domain.parameters import ParameterRevision


@dataclass(frozen=True, slots=True)
class CalculationRequest:
    project_id: UUID
    method_code: str
    method_revision: str
    input_object_ids: tuple[UUID, ...]
    parameter_codes: tuple[str, ...]
    effective_date: date
    jurisdiction_code: str | None = None
    standard_reference_ids: tuple[UUID, ...] = ()
    purpose: CalculationPurpose = CalculationPurpose.ENGINEERING


@dataclass(frozen=True, slots=True)
class CalculationResultDraft:
    result_code: str
    label: str
    value: PropertyValue
    source_object_ids: tuple[UUID, ...] = ()
    source_parameter_codes: tuple[str, ...] = ()
    standard_reference_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class CalculationOutput:
    results: tuple[CalculationResultDraft, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CalculationContext:
    model: EngineeringModel
    request: CalculationRequest
    input_objects: tuple[EngineeringObjectRecord, ...]
    parameters: Mapping[str, ParameterRevision]
    standard_references: tuple[StandardReference, ...]


@dataclass(frozen=True, slots=True)
class CalculationExecution:
    run: CalculationRun
    results: tuple[CalculationResult, ...]
    warnings: tuple[str, ...] = ()
    error: str | None = None


class CalculationEngine(Protocol):
    method_code: str
    method_revision: str
    engine_name: str
    engine_version: str
    required_parameter_codes: tuple[str, ...]

    def calculate(self, context: CalculationContext) -> CalculationOutput:
        """Execute a deterministic calculation using only supplied inputs."""
