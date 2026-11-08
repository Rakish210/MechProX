from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from mechprox.domain.base import IdentifiedModel, PropertyValue, QuantityValue, ScalarValue
from mechprox.domain.enums import InformationOrigin


class ParameterValueKind(StrEnum):
    SCALAR = "scalar"
    QUANTITY = "quantity"


class ParameterScopeKind(StrEnum):
    GLOBAL = "global"
    JURISDICTION = "jurisdiction"
    PROJECT = "project"


class ParameterRevisionStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class ParameterDefinition(IdentifiedModel):
    """Stable identity and dimensional contract for an engineering parameter."""

    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=240)
    discipline_code: str = Field(min_length=1, max_length=80)
    category_code: str = Field(min_length=1, max_length=80)
    value_kind: ParameterValueKind
    expected_dimension: str | None = None
    canonical_unit_code: str | None = None
    description: str | None = None
    source_reference_ids: tuple[UUID, ...] = ()
    standard_reference_ids: tuple[UUID, ...] = ()

    @model_validator(mode="after")
    def validate_value_contract(self) -> "ParameterDefinition":
        if self.value_kind == ParameterValueKind.QUANTITY:
            if not self.expected_dimension or not self.canonical_unit_code:
                raise ValueError(
                    "Quantity parameters require an expected dimension and canonical unit."
                )
        elif self.expected_dimension is not None or self.canonical_unit_code is not None:
            raise ValueError("Scalar parameters cannot declare a physical unit or dimension.")
        return self


class ParameterRevision(IdentifiedModel):
    """Immutable, scoped and time-bounded value revision."""

    definition_id: UUID
    revision_code: str = Field(min_length=1, max_length=80)
    value: PropertyValue
    scope_kind: ParameterScopeKind = ParameterScopeKind.GLOBAL
    scope_key: str = Field(default="", max_length=120)
    status: ParameterRevisionStatus = ParameterRevisionStatus.DRAFT
    valid_from: date | None = None
    valid_to: date | None = None
    origin: InformationOrigin
    source_reference_ids: tuple[UUID, ...] = ()
    standard_reference_ids: tuple[UUID, ...] = ()
    created_by: str = Field(min_length=1, max_length=120)
    approved_by: str | None = Field(default=None, max_length=120)
    change_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    supersedes_revision_id: UUID | None = None

    @model_validator(mode="after")
    def validate_revision(self) -> "ParameterRevision":
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("Parameter valid_to cannot precede valid_from.")
        if self.scope_kind == ParameterScopeKind.GLOBAL and self.scope_key:
            raise ValueError("Global parameter revisions must have an empty scope key.")
        if self.scope_kind != ParameterScopeKind.GLOBAL and not self.scope_key.strip():
            raise ValueError("Jurisdiction and project revisions require a scope key.")
        if self.status == ParameterRevisionStatus.APPROVED and not (
            self.approved_by and self.approved_by.strip()
        ):
            raise ValueError("Approved parameter revisions require an approver.")
        if not isinstance(self.value, (QuantityValue, ScalarValue)):
            raise TypeError("Parameter values must be scalar or unit-bearing quantities.")
        return self


class ParameterRegistry(IdentifiedModel):
    """Portable snapshot of parameter definitions and their immutable revisions."""

    schema_version: str = "1.0"
    definitions: tuple[ParameterDefinition, ...] = ()
    revisions: tuple[ParameterRevision, ...] = ()


class ParameterResolutionError(LookupError):
    pass


def resolve_parameter(
    definition: ParameterDefinition,
    revisions: tuple[ParameterRevision, ...],
    *,
    jurisdiction_code: str | None,
    project_id: UUID | None,
    effective_date: date,
) -> ParameterRevision:
    """Resolve project > jurisdiction > global, considering approved effective revisions only."""
    matches: list[tuple[int, ParameterRevision]] = []
    project_key = str(project_id) if project_id is not None else None

    for revision in revisions:
        if revision.definition_id != definition.id:
            continue
        if revision.status != ParameterRevisionStatus.APPROVED:
            continue
        if revision.valid_from is not None and effective_date < revision.valid_from:
            continue
        if revision.valid_to is not None and effective_date > revision.valid_to:
            continue

        if revision.scope_kind == ParameterScopeKind.PROJECT:
            if project_key is not None and revision.scope_key == project_key:
                matches.append((3, revision))
        elif revision.scope_kind == ParameterScopeKind.JURISDICTION:
            if jurisdiction_code and revision.scope_key == jurisdiction_code:
                matches.append((2, revision))
        else:
            matches.append((1, revision))

    if not matches:
        raise ParameterResolutionError(
            f"No approved effective value exists for parameter '{definition.code}'."
        )

    highest_priority = max(priority for priority, _ in matches)
    selected = [revision for priority, revision in matches if priority == highest_priority]
    if len(selected) != 1:
        raise ParameterResolutionError(
            f"Ambiguous approved values exist for parameter '{definition.code}' "
            f"at scope priority {highest_priority}."
        )
    return selected[0]
