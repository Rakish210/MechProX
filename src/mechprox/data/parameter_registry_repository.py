from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mechprox.data.models import (
    ParameterDefinitionRecord,
    ParameterRevisionRecord,
    SourceReferenceRecord,
    StandardReferenceRecord,
)
from mechprox.domain.base import Quantity, QuantityValue, ScalarValue
from mechprox.domain.parameters import (
    ParameterDefinition,
    ParameterRegistry,
    ParameterRevision,
    ParameterRevisionStatus,
    ParameterValueKind,
    resolve_parameter,
)
from mechprox.domain.units import UnitService, UnitValidationError


class ParameterAlreadyExistsError(ValueError):
    pass


class ParameterDefinitionNotFoundError(LookupError):
    pass


class ParameterRegistryRepository:
    """SQLite-backed repository for immutable, source-traceable parameter revisions."""

    def __init__(
        self,
        session_factory: sessionmaker,
        unit_service: UnitService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._units = unit_service or UnitService()

    def register_definition(self, definition: ParameterDefinition) -> None:
        self._validate_definition(definition)
        record = ParameterDefinitionRecord(
            id=str(definition.id),
            code=definition.code,
            discipline_code=definition.discipline_code,
            category_code=definition.category_code,
            model_json=definition.model_dump_json(),
            created_at=datetime.now(UTC),
        )
        try:
            with self._session_factory.begin() as session:
                self._validate_references(
                    session,
                    definition.source_reference_ids,
                    definition.standard_reference_ids,
                )
                session.add(record)
                session.flush()
        except IntegrityError as exc:
            raise ParameterAlreadyExistsError(
                f"Parameter code '{definition.code}' already exists."
            ) from exc

    def add_revision(self, revision: ParameterRevision) -> None:
        with self._session_factory.begin() as session:
            definition_record = session.get(
                ParameterDefinitionRecord, str(revision.definition_id)
            )
            if definition_record is None:
                raise ParameterDefinitionNotFoundError(
                    f"Parameter definition '{revision.definition_id}' was not found."
                )
            definition = ParameterDefinition.model_validate_json(
                definition_record.model_json
            )
            self._validate_value(definition, revision)
            self._validate_references(
                session,
                revision.source_reference_ids,
                revision.standard_reference_ids,
            )
            record = ParameterRevisionRecord(
                id=str(revision.id),
                definition_id=str(revision.definition_id),
                revision_code=revision.revision_code,
                scope_kind=revision.scope_kind.value,
                scope_key=revision.scope_key,
                status=revision.status.value,
                valid_from=revision.valid_from,
                valid_to=revision.valid_to,
                model_json=revision.model_dump_json(),
                created_at=revision.created_at,
            )
            session.add(record)
            session.flush()

    def get_definition(self, code: str) -> ParameterDefinition:
        with self._session_factory() as session:
            record = session.scalar(
                select(ParameterDefinitionRecord).where(
                    ParameterDefinitionRecord.code == code
                )
            )
            if record is None:
                raise ParameterDefinitionNotFoundError(
                    f"Parameter definition '{code}' was not found."
                )
            payload = record.model_json
        return ParameterDefinition.model_validate_json(payload)

    def list_definitions(self) -> tuple[ParameterDefinition, ...]:
        with self._session_factory() as session:
            records = session.scalars(
                select(ParameterDefinitionRecord).order_by(
                    ParameterDefinitionRecord.discipline_code,
                    ParameterDefinitionRecord.category_code,
                    ParameterDefinitionRecord.code,
                )
            ).all()
            return tuple(
                ParameterDefinition.model_validate_json(record.model_json)
                for record in records
            )

    def resolve(
        self,
        code: str,
        *,
        jurisdiction_code: str | None,
        project_id: UUID | None,
        effective_date: date,
    ) -> ParameterRevision:
        definition = self.get_definition(code)
        with self._session_factory() as session:
            records = session.scalars(
                select(ParameterRevisionRecord).where(
                    ParameterRevisionRecord.definition_id == str(definition.id),
                    ParameterRevisionRecord.status
                    == ParameterRevisionStatus.APPROVED.value,
                )
            ).all()
            revisions = tuple(
                ParameterRevision.model_validate_json(record.model_json)
                for record in records
            )
        selected = resolve_parameter(
            definition,
            revisions,
            jurisdiction_code=jurisdiction_code,
            project_id=project_id,
            effective_date=effective_date,
        )
        return selected.model_copy(
            update={
                "source_reference_ids": tuple(
                    dict.fromkeys(
                        (*definition.source_reference_ids, *selected.source_reference_ids)
                    )
                ),
                "standard_reference_ids": tuple(
                    dict.fromkeys(
                        (*definition.standard_reference_ids, *selected.standard_reference_ids)
                    )
                ),
            }
        )

    def export_snapshot(self) -> ParameterRegistry:
        definitions = self.list_definitions()
        with self._session_factory() as session:
            records = session.scalars(
                select(ParameterRevisionRecord).order_by(
                    ParameterRevisionRecord.definition_id,
                    ParameterRevisionRecord.created_at,
                )
            ).all()
            revisions = tuple(
                ParameterRevision.model_validate_json(record.model_json)
                for record in records
            )
        return ParameterRegistry(definitions=definitions, revisions=revisions)

    @staticmethod
    def _validate_references(
        session: Session,
        source_ids: tuple[UUID, ...],
        standard_ids: tuple[UUID, ...],
    ) -> None:
        for source_id in source_ids:
            if session.get(SourceReferenceRecord, str(source_id)) is None:
                raise ValueError(f"Unknown source reference '{source_id}'.")
        for standard_id in standard_ids:
            if session.get(StandardReferenceRecord, str(standard_id)) is None:
                raise ValueError(f"Unknown standard reference '{standard_id}'.")

    def _validate_definition(self, definition: ParameterDefinition) -> None:
        if definition.value_kind == ParameterValueKind.SCALAR:
            return
        try:
            self._units.validate(
                Quantity(
                    value=Decimal(1),
                    unit_code=definition.canonical_unit_code or "",
                ),
                expected_dimension=definition.expected_dimension,
            )
        except UnitValidationError as exc:
            raise ValueError(
                f"Parameter '{definition.code}' has an invalid canonical unit: {exc}"
            ) from exc

    def _validate_value(
        self,
        definition: ParameterDefinition,
        revision: ParameterRevision,
    ) -> None:
        value = revision.value
        if definition.value_kind == ParameterValueKind.SCALAR:
            if not isinstance(value, ScalarValue):
                raise ValueError(
                    f"Parameter '{definition.code}' requires a scalar value."
                )
            return
        if not isinstance(value, QuantityValue):
            raise TypeError(
                f"Parameter '{definition.code}' requires a unit-bearing quantity."
            )
        try:
            self._units.validate(
                value.quantity,
                expected_dimension=definition.expected_dimension,
            )
        except UnitValidationError as exc:
            raise ValueError(
                f"Parameter '{definition.code}' has an invalid quantity: {exc}"
            ) from exc
        if not self._units.are_compatible(
            value.quantity.unit_code,
            definition.canonical_unit_code or "",
        ):
            raise ValueError(
                f"Parameter '{definition.code}' requires a unit compatible with "
                f"'{definition.canonical_unit_code}'."
            )
