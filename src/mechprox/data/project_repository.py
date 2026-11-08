from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from mechprox.data.models import ProjectSnapshotRecord
from mechprox.domain.calculations import CalculationResult, CalculationRun
from mechprox.domain.commercial import BOMDocument, BOQDocument
from mechprox.domain.model import EngineeringModel
from mechprox.domain.serialization import deserialize_model, serialize_model
from mechprox.domain.validation import ModelValidator


class ProjectAlreadyExistsError(ValueError):
    """Raised when a project code is already in use."""


class ProjectNotFoundError(LookupError):
    """Raised when a project snapshot cannot be found."""


class CalculationAppendError(ValueError):
    """Raised when a calculation execution cannot be appended safely."""


class CommercialAppendError(ValueError):
    """Raised when a takeoff document cannot be appended to the current model."""


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

    def append_commercial_documents(
        self,
        expected_model: EngineeringModel,
        bom: BOMDocument,
        boq: BOQDocument,
    ) -> ProjectSummary:
        """Atomically append takeoff documents only if the source model is unchanged."""
        project_id = expected_model.project.id
        if bom.project_id != project_id or boq.project_id != project_id:
            raise CommercialAppendError("BOM and BOQ must belong to the target project.")
        if any(item.id == bom.id for item in expected_model.bom_documents):
            raise CommercialAppendError("BOM document already exists in the expected model.")
        if any(item.id == boq.id for item in expected_model.boq_documents):
            raise CommercialAppendError("BOQ document already exists in the expected model.")

        with self._session_factory.begin() as session:
            record = session.get(ProjectSnapshotRecord, str(project_id))
            if record is None:
                raise ProjectNotFoundError(f"Project '{project_id}' was not found.")
            current_model = deserialize_model(record.model_json)
            if current_model != expected_model:
                raise CommercialAppendError(
                    "The project changed while takeoff was being prepared. "
                    "Refresh the project and generate BOM/BOQ again."
                )
            updated_model = current_model.model_copy(
                update={
                    "bom_documents": (*current_model.bom_documents, bom),
                    "boq_documents": (*current_model.boq_documents, boq),
                }
            )
            ModelValidator().validate(updated_model).raise_for_errors()
            record.schema_version = updated_model.schema_version
            record.model_json = serialize_model(updated_model)
            record.updated_at = datetime.now(UTC)
            session.flush()
            return self._summary(record)

    def append_calculation_execution(
        self,
        project_id: UUID,
        run: CalculationRun,
        results: tuple[CalculationResult, ...],
    ) -> ProjectSummary:
        """Atomically append a calculation to the latest stored project snapshot.

        The supplied calculation input may have been prepared from an older in-memory
        model. Loading and updating the current snapshot inside one transaction avoids
        overwriting unrelated project edits made while the calculation was running.
        """
        if run.project_id != project_id:
            raise CalculationAppendError(
                "Calculation run project does not match the target project."
            )
        if any(result.calculation_run_id != run.id for result in results):
            raise CalculationAppendError(
                "Every calculation result must reference the appended calculation run."
            )

        with self._session_factory.begin() as session:
            record = session.get(ProjectSnapshotRecord, str(project_id))
            if record is None:
                raise ProjectNotFoundError(f"Project '{project_id}' was not found.")

            current_model = deserialize_model(record.model_json)
            if current_model.project.id != project_id:
                raise CalculationAppendError(
                    "Stored project identity does not match its persistence key."
                )
            if any(existing.id == run.id for existing in current_model.calculation_runs):
                raise CalculationAppendError(
                    f"Calculation run '{run.id}' has already been appended."
                )

            current_objects = {item.id: item for item in current_model.objects}
            for snapshot in run.input_snapshots:
                current_object = current_objects.get(snapshot.engineering_object_id)
                if (
                    current_object is None
                    or current_object.revision_id != snapshot.object_revision_id
                    or (
                        snapshot.object_snapshot is not None
                        and current_object != snapshot.object_snapshot
                    )
                ):
                    raise CalculationAppendError(
                        "Calculation input object "
                        f"'{snapshot.engineering_object_id}' changed after the run inputs "
                        "were captured. Recalculate against the current project model."
                    )

            existing_result_ids = {
                result.id for result in current_model.calculation_results
            }
            if any(result.id in existing_result_ids for result in results):
                raise CalculationAppendError(
                    "A calculation result ID already exists in the project."
                )

            updated_model = current_model.model_copy(
                update={
                    "calculation_runs": (*current_model.calculation_runs, run),
                    "calculation_results": (
                        *current_model.calculation_results,
                        *results,
                    ),
                }
            )
            record.schema_version = updated_model.schema_version
            record.model_json = serialize_model(updated_model)
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
