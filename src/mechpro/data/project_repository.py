from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from mechpro.data.models import ProjectSnapshotRecord
from mechpro.domain.model import EngineeringModel
from mechpro.domain.serialization import deserialize_model, serialize_model


class ProjectAlreadyExistsError(ValueError):
    """Raised when a project code is already in use."""


class ProjectNotFoundError(LookupError):
    """Raised when a project snapshot cannot be found."""


@dataclass(frozen=True, slots=True)
class ProjectSummary:
    id: UUID
    project_code: str
    name: str
    schema_version: str
    updated_at: datetime


class ProjectRepository:
    """Persistence boundary for complete, validated engineering-model snapshots."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def create(self, model: EngineeringModel) -> ProjectSummary:
        now = datetime.now(UTC)
        record = ProjectSnapshotRecord(
            id=str(model.project.id),
            project_code=model.project.project_code,
            name=model.project.name,
            schema_version=model.schema_version,
            model_json=serialize_model(model),
            created_at=now,
            updated_at=now,
        )
        try:
            with self._session_factory.begin() as session:
                session.add(record)
                session.flush()
        except IntegrityError as exc:
            raise ProjectAlreadyExistsError(
                f"Project code '{model.project.project_code}' is already in use."
            ) from exc
        return self._summary(record)

    def get(self, project_id: UUID) -> EngineeringModel:
        with self._session_factory() as session:
            record = session.get(ProjectSnapshotRecord, str(project_id))
            if record is None:
                raise ProjectNotFoundError(f"Project '{project_id}' was not found.")
            payload = record.model_json
        return deserialize_model(payload)

    def list(self) -> tuple[ProjectSummary, ...]:
        with self._session_factory() as session:
            records = session.scalars(
                select(ProjectSnapshotRecord).order_by(ProjectSnapshotRecord.updated_at.desc())
            ).all()
            return tuple(self._summary(record) for record in records)

    def save(self, model: EngineeringModel) -> ProjectSummary:
        with self._session_factory.begin() as session:
            record = session.get(ProjectSnapshotRecord, str(model.project.id))
            if record is None:
                raise ProjectNotFoundError(f"Project '{model.project.id}' was not found.")
            record.project_code = model.project.project_code
            record.name = model.project.name
            record.schema_version = model.schema_version
            record.model_json = serialize_model(model)
            record.updated_at = datetime.now(UTC)
            session.flush()
            return self._summary(record)

    @staticmethod
    def _summary(record: ProjectSnapshotRecord) -> ProjectSummary:
        return ProjectSummary(
            id=UUID(record.id),
            project_code=record.project_code,
            name=record.name,
            schema_version=record.schema_version,
            updated_at=record.updated_at,
        )
