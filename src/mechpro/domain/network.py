from uuid import UUID

from pydantic import Field

from mechpro.domain.base import IdentifiedModel
from mechpro.domain.engineering import ConnectorEndpoint
from mechpro.domain.enums import (
    ConnectionDirection,
    ConnectionKind,
    InformationOrigin,
)


class Network(IdentifiedModel):
    """A connected graph; it may branch, loop, or contain non-linear relationships."""

    project_id: UUID
    system_id: UUID
    network_code: str = Field(min_length=1)
    name: str
    network_type: str
    member_object_ids: tuple[UUID, ...]
    connection_ids: tuple[UUID, ...] = ()
    source_reference_ids: tuple[UUID, ...] = ()


class Connection(IdentifiedModel):
    network_id: UUID
    from_endpoint: ConnectorEndpoint
    to_endpoint: ConnectorEndpoint
    connection_kind: ConnectionKind
    direction: ConnectionDirection = ConnectionDirection.BIDIRECTIONAL
    origin: InformationOrigin
    source_reference_ids: tuple[UUID, ...] = ()
    revision_id: UUID | None = None
