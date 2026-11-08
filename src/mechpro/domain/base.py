from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mechpro.domain.enums import (
    ApprovalDecision,
    GeometryFormat,
    InformationOrigin,
    RevisionState,
    SourceKind,
)


class DomainModel(BaseModel):
    """Immutable, strictly typed domain contract.

    Unknown fields are rejected intentionally: domain records must not become
    unstructured JSON property bags.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class IdentifiedModel(DomainModel):
    id: UUID = Field(default_factory=uuid4)


class Quantity(DomainModel):
    """A numeric magnitude and an explicit unit identifier."""

    value: Decimal
    unit_code: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("Quantity magnitude must be finite.")
        return value

    @field_validator("unit_code")
    @classmethod
    def unit_code_must_be_nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A quantity must declare a unit.")
        return value


class ScalarValue(DomainModel):
    kind: Literal["scalar"] = "scalar"
    value: Decimal | int | float | bool | str


class QuantityValue(DomainModel):
    kind: Literal["quantity"] = "quantity"
    quantity: Quantity


class ReferenceValue(DomainModel):
    kind: Literal["reference"] = "reference"
    target_id: UUID


PropertyValue = Annotated[
    ScalarValue | QuantityValue | ReferenceValue,
    Field(discriminator="kind"),
]


class EngineeringProperty(IdentifiedModel):
    key: str = Field(min_length=1)
    value: PropertyValue
    origin: InformationOrigin
    source_reference_ids: tuple[UUID, ...] = ()
    standard_reference_id: UUID | None = None
    revision_id: UUID | None = None
    note: str | None = None

    @field_validator("key")
    @classmethod
    def key_must_be_nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Property key cannot be blank.")
        return value


class SourceReference(IdentifiedModel):
    """Trace to a source document and, where available, a native source entity."""

    source_kind: SourceKind
    uri: str | None = None
    document_name: str | None = None
    document_revision: str | None = None
    external_entity_id: str | None = None
    entity_handle: str | None = None
    element_unique_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    sheet_name: str | None = None
    content_hash: str | None = None
    origin: InformationOrigin
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GeometryReference(IdentifiedModel):
    """Reference to external geometry; native CAD/BIM geometry is not copied here."""

    format: GeometryFormat
    file_uri: str
    geometry_type: str
    external_entity_id: str | None = None
    coordinate_system: str | None = None
    source_reference_id: UUID | None = None
    geometry_hash: str | None = None
    transform_matrix: tuple[float, ...] = ()

    @field_validator("transform_matrix")
    @classmethod
    def transform_matrix_must_be_empty_or_4x4(
        cls, value: tuple[float, ...]
    ) -> tuple[float, ...]:
        if value and len(value) != 16:
            raise ValueError("A transform matrix must contain exactly 16 values.")
        return value


class StandardReference(IdentifiedModel):
    standard_code: str = Field(min_length=1)
    title: str
    edition: str
    jurisdiction: str | None = None
    clause: str | None = None
    published_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    source_reference_id: UUID | None = None

    @model_validator(mode="after")
    def effective_dates_must_be_ordered(self) -> StandardReference:
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("Standard effective_to cannot precede effective_from.")
        return self


class Revision(IdentifiedModel):
    """Immutable revision identity for a project, model object or controlled record."""

    object_id: UUID
    revision_code: str = Field(min_length=1)
    state: RevisionState
    content_hash: str | None = None
    parent_revision_id: UUID | None = None
    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    changed_by: str
    change_summary: str | None = None


class ApprovalRecord(IdentifiedModel):
    revision_id: UUID
    decision: ApprovalDecision
    approver: str
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    comment: str | None = None
