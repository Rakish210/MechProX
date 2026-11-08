from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field, model_validator

from mechprox.domain.base import IdentifiedModel, Quantity
from mechprox.domain.enums import InformationOrigin


class ProductReference(IdentifiedModel):
    """Physical product/material reference used by BOM and procurement."""

    catalogue_code: str
    product_code: str
    name: str
    category_code: str
    unit_code: str
    manufacturer: str | None = None
    catalogue_revision: str | None = None
    source_reference_ids: tuple[UUID, ...] = ()
    origin: InformationOrigin


class PositionReference(IdentifiedModel):
    """Commercial BOQ/public-works position; deliberately separate from products."""

    catalogue_code: str
    position_code: str
    name: str
    unit_code: str
    jurisdiction: str | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    currency_code: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    source_reference_ids: tuple[UUID, ...] = ()
    catalogue_revision: str | None = None

    @model_validator(mode="after")
    def validity_dates_must_be_ordered(self) -> "PositionReference":
        if self.valid_from is not None and self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("Position valid_to cannot precede valid_from.")
        return self


class PositionProductMapping(IdentifiedModel):
    """Versioned many-to-many relationship between BOQ positions and products."""

    position_reference_id: UUID
    product_reference_id: UUID
    mapping_code: str
    mapping_version: str
    measurement_rule_code: str
    source_reference_ids: tuple[UUID, ...] = ()
    valid_from: date | None = None
    valid_to: date | None = None
    enabled: bool = True

    @model_validator(mode="after")
    def validity_dates_must_be_ordered(self) -> "PositionProductMapping":
        if self.valid_from is not None and self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("Mapping valid_to cannot precede valid_from.")
        return self


class BOMItem(IdentifiedModel):
    product_reference_id: UUID
    quantity: Quantity
    source_object_ids: tuple[UUID, ...]
    note: str | None = None


class BOMDocument(IdentifiedModel):
    project_id: UUID
    title: str
    model_revision_id: UUID | None = None
    items: tuple[BOMItem, ...]
    prepared_at: date = Field(default_factory=date.today)


class BOQItem(IdentifiedModel):
    position_reference_id: UUID
    quantity: Quantity
    source_object_ids: tuple[UUID, ...]
    mapping_id: UUID
    measurement_rule_code: str
    measurement_rule_version: str
    measurement_note: str | None = None


class BOQDocument(IdentifiedModel):
    project_id: UUID
    title: str
    model_revision_id: UUID | None = None
    items: tuple[BOQItem, ...]
    prepared_at: date = Field(default_factory=date.today)
