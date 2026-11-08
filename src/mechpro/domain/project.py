from uuid import UUID

from pydantic import Field

from mechpro.domain.base import IdentifiedModel, Quantity
from mechpro.domain.enums import ValidationStatus


class Project(IdentifiedModel):
    project_code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    client_name: str | None = None
    coordinate_system: str | None = None
    validation_status: ValidationStatus = ValidationStatus.NOT_CHECKED


class Building(IdentifiedModel):
    project_id: UUID
    building_code: str = Field(min_length=1)
    name: str
    description: str | None = None


class Level(IdentifiedModel):
    building_id: UUID
    level_code: str = Field(min_length=1)
    name: str
    elevation: Quantity | None = None


class Space(IdentifiedModel):
    level_id: UUID
    space_code: str = Field(min_length=1)
    name: str
    area: Quantity | None = None
    volume: Quantity | None = None
    usage: str | None = None


class Discipline(IdentifiedModel):
    """Extensible discipline taxonomy entry; codes are data, not a closed enum."""

    code: str = Field(min_length=1)
    name: str
    description: str | None = None


class EngineeringSystem(IdentifiedModel):
    project_id: UUID
    discipline_code: str = Field(min_length=1)
    system_code: str = Field(min_length=1)
    name: str
    system_family: str
    description: str | None = None
