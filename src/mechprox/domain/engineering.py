from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from mechprox.domain.base import DomainModel, EngineeringProperty, IdentifiedModel, Quantity
from mechprox.domain.enums import (
    ConnectorDirection,
    ConnectorDomain,
    InformationOrigin,
    ValidationStatus,
)


class Connector(IdentifiedModel):
    """A typed connection port owned by an engineering object."""

    code: str = Field(min_length=1)
    domain: ConnectorDomain
    direction: ConnectorDirection = ConnectorDirection.UNSPECIFIED
    nominal_size: str | None = None
    compatibility_code: str | None = None


class ConnectorEndpoint(DomainModel):
    object_id: UUID
    connector_id: UUID


class EngineeringObject(IdentifiedModel):
    kind: Literal["object"] = "object"
    project_id: UUID
    name: str
    category_code: str
    discipline_code: str
    system_id: UUID | None = None
    level_id: UUID | None = None
    properties: tuple[EngineeringProperty, ...] = ()
    connectors: tuple[Connector, ...] = ()
    geometry_reference_ids: tuple[UUID, ...] = ()
    source_reference_ids: tuple[UUID, ...] = ()
    revision_id: UUID | None = None
    position_mapping_id: UUID | None = None
    information_origin: InformationOrigin
    validation_status: ValidationStatus = ValidationStatus.NOT_CHECKED


class Equipment(EngineeringObject):
    kind: Literal["equipment"] = "equipment"
    equipment_type: str
    product_reference_id: UUID | None = None
    manufacturer: str | None = None
    model_code: str | None = None


class LinearElement(EngineeringObject):
    kind: Literal["linear_element"] = "linear_element"
    element_type: str
    length: Quantity
    nominal_size: str | None = None
    material_product_reference_id: UUID | None = None


EngineeringObjectRecord = Annotated[
    EngineeringObject | Equipment | LinearElement,
    Field(discriminator="kind"),
]
