from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.data import models  # noqa: F401
from mechprox.data.db import Base
from mechprox.data.source_registry_repository import (
    SourceReferenceNotFoundError,
    SourceRegistryConflictError,
    SourceRegistryRepository,
)
from mechprox.domain.base import SourceReference, StandardReference
from mechprox.domain.enums import InformationOrigin, SourceKind


@pytest.fixture
def repository(tmp_path: Path) -> SourceRegistryRepository:
    engine = create_engine(f"sqlite:///{tmp_path / 'sources.db'}")
    Base.metadata.create_all(engine)
    return SourceRegistryRepository(sessionmaker(bind=engine, expire_on_commit=False))


def _source() -> SourceReference:
    return SourceReference(
        source_kind=SourceKind.STANDARD,
        uri="https://example.invalid/standard.pdf",
        document_name="Engineering Standard",
        document_revision="2024 edition",
        content_hash="sha256:abc123",
        origin=InformationOrigin.USER_INPUT,
    )


def _standard(source_id) -> StandardReference:
    return StandardReference(
        standard_code="EN 12345",
        title="Example engineering requirements",
        edition="2024",
        jurisdiction="EU",
        clause="6.2.1",
        source_reference_id=source_id,
    )


def test_source_and_standard_round_trip(repository: SourceRegistryRepository) -> None:
    source = _source()
    standard = _standard(source.id)

    repository.register_source(source)
    repository.register_standard(standard)
    snapshot = repository.export_snapshot()

    assert snapshot.sources == (source,)
    assert snapshot.standards == (standard,)


def test_standard_requires_registered_source(repository: SourceRegistryRepository) -> None:
    with pytest.raises(SourceReferenceNotFoundError):
        repository.register_standard(_standard(uuid4()))


def test_duplicate_standard_clause_is_rejected(
    repository: SourceRegistryRepository,
) -> None:
    source = _source()
    repository.register_source(source)
    standard = _standard(source.id)
    repository.register_standard(standard)

    with pytest.raises(SourceRegistryConflictError):
        repository.register_standard(standard.model_copy(update={"id": uuid4()}))
