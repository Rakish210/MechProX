from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from mechprox.data.models import SourceReferenceRecord, StandardReferenceRecord
from mechprox.domain.base import SourceReference, StandardReference


class SourceRegistryConflictError(ValueError):
    """Raised when a standard edition/clause already exists."""


class SourceReferenceNotFoundError(LookupError):
    """Raised when a standard refers to a source that is not registered."""


@dataclass(frozen=True, slots=True)
class SourceRegistrySnapshot:
    sources: tuple[SourceReference, ...]
    standards: tuple[StandardReference, ...]


class SourceRegistryRepository:
    """Global immutable source and standard-reference registry."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def register_source(self, source: SourceReference) -> SourceReference:
        if not (source.uri or source.document_name):
            raise ValueError("A source reference requires a document name or URI.")
        record = SourceReferenceRecord(
            id=str(source.id),
            source_kind=source.source_kind.value,
            document_name=source.document_name,
            document_revision=source.document_revision,
            uri=source.uri,
            content_hash=source.content_hash,
            model_json=source.model_dump_json(),
            captured_at=source.captured_at,
            created_at=datetime.now(UTC),
        )
        with self._session_factory.begin() as session:
            session.add(record)
            session.flush()
        return source

    def register_standard(self, standard: StandardReference) -> StandardReference:
        if not all((standard.standard_code.strip(), standard.title.strip(), standard.edition.strip())):
            raise ValueError("A standard reference requires a code, title and edition.")
        with self._session_factory.begin() as session:
            if standard.source_reference_id is not None and session.get(
                SourceReferenceRecord, str(standard.source_reference_id)
            ) is None:
                raise SourceReferenceNotFoundError(
                    f"Source reference '{standard.source_reference_id}' was not found."
                )
            session.add(
                StandardReferenceRecord(
                    id=str(standard.id),
                    standard_code=standard.standard_code,
                    edition=standard.edition,
                    jurisdiction=standard.jurisdiction or "",
                    clause=standard.clause or "",
                    title=standard.title,
                    source_reference_id=(
                        str(standard.source_reference_id)
                        if standard.source_reference_id
                        else None
                    ),
                    model_json=standard.model_dump_json(),
                    created_at=datetime.now(UTC),
                )
            )
            try:
                session.flush()
            except IntegrityError as exc:
                raise SourceRegistryConflictError(
                    f"Standard '{standard.standard_code}' edition '{standard.edition}' "
                    f"clause '{standard.clause or '-'}' already exists for "
                    f"jurisdiction '{standard.jurisdiction or 'global'}'."
                ) from exc
        return standard

    def get_source(self, source_id: UUID) -> SourceReference:
        with self._session_factory() as session:
            record = session.get(SourceReferenceRecord, str(source_id))
            if record is None:
                raise SourceReferenceNotFoundError(f"Source reference '{source_id}' was not found.")
            payload = record.model_json
        return SourceReference.model_validate_json(payload)

    def list_sources(self) -> tuple[SourceReference, ...]:
        with self._session_factory() as session:
            records = session.scalars(
                select(SourceReferenceRecord).order_by(
                    SourceReferenceRecord.document_name,
                    SourceReferenceRecord.document_revision,
                )
            ).all()
            return tuple(SourceReference.model_validate_json(row.model_json) for row in records)

    def list_standards(self) -> tuple[StandardReference, ...]:
        with self._session_factory() as session:
            records = session.scalars(
                select(StandardReferenceRecord).order_by(
                    StandardReferenceRecord.standard_code,
                    StandardReferenceRecord.edition,
                    StandardReferenceRecord.clause,
                )
            ).all()
            return tuple(StandardReference.model_validate_json(row.model_json) for row in records)

    def get_standard(self, standard_id: UUID) -> StandardReference:
        with self._session_factory() as session:
            record = session.get(StandardReferenceRecord, str(standard_id))
            if record is None:
                raise LookupError(f"Standard reference '{standard_id}' was not found.")
            payload = record.model_json
        return StandardReference.model_validate_json(payload)

    def export_snapshot(self) -> SourceRegistrySnapshot:
        return SourceRegistrySnapshot(
            sources=self.list_sources(),
            standards=self.list_standards(),
        )
