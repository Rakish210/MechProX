from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.data import models  # noqa: F401
from mechprox.data.db import Base
from mechprox.data.parameter_registry_repository import (
    ParameterAlreadyExistsError,
    ParameterRegistryRepository,
)
from mechprox.data.source_registry_repository import SourceRegistryRepository
from mechprox.domain.base import (
    Quantity,
    QuantityValue,
    ScalarValue,
    SourceReference,
    StandardReference,
)
from mechprox.domain.enums import InformationOrigin, SourceKind
from mechprox.domain.parameters import (
    ParameterDefinition,
    ParameterResolutionError,
    ParameterRevision,
    ParameterRevisionStatus,
    ParameterScopeKind,
    ParameterValueKind,
)


@pytest.fixture
def repository(tmp_path) -> ParameterRegistryRepository:
    engine = create_engine(f"sqlite:///{tmp_path / 'parameters.db'}")
    Base.metadata.create_all(engine)
    return ParameterRegistryRepository(
        sessionmaker(bind=engine, expire_on_commit=False)
    )


def _definition() -> ParameterDefinition:
    return ParameterDefinition(
        code="GAS.TEST_PRESSURE",
        name="Test pressure",
        discipline_code="GAS",
        category_code="PRESSURE",
        value_kind=ParameterValueKind.QUANTITY,
        expected_dimension="[pressure]",
        canonical_unit_code="bar",
    )


def _revision(
    definition: ParameterDefinition,
    value: Decimal,
    *,
    scope: ParameterScopeKind = ParameterScopeKind.GLOBAL,
    scope_key: str = "",
    revision_code: str = "A",
) -> ParameterRevision:
    return ParameterRevision(
        definition_id=definition.id,
        revision_code=revision_code,
        value=QuantityValue(quantity=Quantity(value=value, unit_code="bar")),
        scope_kind=scope,
        scope_key=scope_key,
        status=ParameterRevisionStatus.APPROVED,
        origin=InformationOrigin.USER_INPUT,
        created_by="test",
        approved_by="test-approver",
    )


def test_parameter_registry_resolves_project_override(
    repository: ParameterRegistryRepository,
) -> None:
    definition = _definition()
    project_id = uuid4()
    repository.register_definition(definition)
    repository.add_revision(_revision(definition, Decimal("1.0")))
    repository.add_revision(
        _revision(
            definition,
            Decimal("2.0"),
            scope=ParameterScopeKind.JURISDICTION,
            scope_key="KZ",
        )
    )
    project_revision = _revision(
        definition,
        Decimal("3.0"),
        scope=ParameterScopeKind.PROJECT,
        scope_key=str(project_id),
    )
    repository.add_revision(project_revision)

    resolved = repository.resolve(
        definition.code,
        jurisdiction_code="KZ",
        project_id=project_id,
        effective_date=date(2026, 11, 8),
    )

    assert resolved.id == project_revision.id
    assert isinstance(resolved.value, QuantityValue)
    assert resolved.value.quantity.value == Decimal("3.0")


def test_parameter_registry_falls_back_to_jurisdiction(
    repository: ParameterRegistryRepository,
) -> None:
    definition = _definition()
    repository.register_definition(definition)
    repository.add_revision(_revision(definition, Decimal("1.0")))
    regional = _revision(
        definition,
        Decimal("2.0"),
        scope=ParameterScopeKind.JURISDICTION,
        scope_key="KZ",
    )
    repository.add_revision(regional)

    resolved = repository.resolve(
        definition.code,
        jurisdiction_code="KZ",
        project_id=None,
        effective_date=date(2026, 11, 8),
    )

    assert resolved.id == regional.id


def test_unapproved_values_are_not_resolved(
    repository: ParameterRegistryRepository,
) -> None:
    definition = _definition()
    repository.register_definition(definition)
    draft = _revision(definition, Decimal("1.0")).model_copy(
        update={"status": ParameterRevisionStatus.DRAFT, "approved_by": None}
    )
    repository.add_revision(draft)

    with pytest.raises(ParameterResolutionError):
        repository.resolve(
            definition.code,
            jurisdiction_code=None,
            project_id=None,
            effective_date=date(2026, 11, 8),
        )


def test_parameter_value_dimension_is_enforced(
    repository: ParameterRegistryRepository,
) -> None:
    definition = _definition()
    repository.register_definition(definition)
    invalid = _revision(definition, Decimal("10.0")).model_copy(
        update={
            "value": QuantityValue(
                quantity=Quantity(value=Decimal(10), unit_code="meter")
            )
        }
    )

    with pytest.raises(ValueError, match="invalid quantity"):
        repository.add_revision(invalid)


def test_duplicate_parameter_code_is_rejected(
    repository: ParameterRegistryRepository,
) -> None:
    definition = _definition()
    repository.register_definition(definition)

    with pytest.raises(ParameterAlreadyExistsError):
        repository.register_definition(definition.model_copy(update={"id": uuid4()}))



def test_invalid_canonical_unit_is_rejected(repository: ParameterRegistryRepository) -> None:
    definition = ParameterDefinition(
        code="GAS.INVALID_UNIT",
        name="Invalid unit test",
        discipline_code="GAS",
        category_code="PRESSURE",
        value_kind=ParameterValueKind.QUANTITY,
        expected_dimension="[pressure]",
        canonical_unit_code="meter",
    )

    with pytest.raises(ValueError, match="invalid canonical unit"):
        repository.register_definition(definition)


def test_ambiguous_approved_revisions_are_rejected(
    repository: ParameterRegistryRepository,
) -> None:
    definition = _definition()
    repository.register_definition(definition)
    repository.add_revision(_revision(definition, Decimal("1.0"), revision_code="A"))
    repository.add_revision(_revision(definition, Decimal("2.0"), revision_code="B"))

    with pytest.raises(ParameterResolutionError, match="Ambiguous"):
        repository.resolve(
            definition.code,
            jurisdiction_code=None,
            project_id=None,
            effective_date=date(2026, 11, 8),
        )


def test_scalar_parameter_can_be_resolved(repository: ParameterRegistryRepository) -> None:
    definition = ParameterDefinition(
        code="VENTILATION.TEST_FACTOR",
        name="Scalar test factor",
        discipline_code="VENTILATION",
        category_code="FACTOR",
        value_kind=ParameterValueKind.SCALAR,
    )
    repository.register_definition(definition)
    revision = ParameterRevision(
        definition_id=definition.id,
        revision_code="A",
        value=ScalarValue(value=Decimal("0.85")),
        status=ParameterRevisionStatus.APPROVED,
        origin=InformationOrigin.USER_INPUT,
        created_by="test",
        approved_by="test-approver",
    )
    repository.add_revision(revision)

    resolved = repository.resolve(
        definition.code,
        jurisdiction_code=None,
        project_id=None,
        effective_date=date(2026, 11, 8),
    )

    assert resolved.id == revision.id
    assert isinstance(resolved.value, ScalarValue)
    assert resolved.value.value == Decimal("0.85")


def test_parameter_definition_references_must_exist_in_source_registry(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'parameter-sources.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ParameterRegistryRepository(factory)
    missing_source_id = uuid4()
    definition = ParameterDefinition(
        code="TEST.SOURCE_LINK",
        name="Source-linked scalar",
        discipline_code="GENERAL",
        category_code="TEST",
        value_kind=ParameterValueKind.SCALAR,
        source_reference_ids=(missing_source_id,),
    )

    with pytest.raises(ValueError, match="Unknown source reference"):
        repository.register_definition(definition)


def test_parameter_resolution_inherits_definition_provenance(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'parameter-provenance.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    repository = ParameterRegistryRepository(factory)
    source_repository = SourceRegistryRepository(factory)
    source = SourceReference(
        source_kind=SourceKind.STANDARD,
        document_name="Engineering standard",
        document_revision="2024",
        uri="https://example.invalid/standard.pdf",
        origin=InformationOrigin.USER_INPUT,
    )
    source_repository.register_source(source)
    standard = StandardReference(
        standard_code="EN 10000",
        title="Test standard",
        edition="2024",
        clause="4.1",
        source_reference_id=source.id,
    )
    source_repository.register_standard(standard)
    definition = ParameterDefinition(
        code="TEST.PROVENANCE",
        name="Provenance test",
        discipline_code="GENERAL",
        category_code="TEST",
        value_kind=ParameterValueKind.SCALAR,
        source_reference_ids=(source.id,),
        standard_reference_ids=(standard.id,),
    )
    repository.register_definition(definition)
    revision = ParameterRevision(
        definition_id=definition.id,
        revision_code="A",
        value=ScalarValue(value=Decimal("1.5")),
        status=ParameterRevisionStatus.APPROVED,
        origin=InformationOrigin.USER_INPUT,
        created_by="test",
        approved_by="test",
    )
    repository.add_revision(revision)

    resolved = repository.resolve(
        definition.code,
        jurisdiction_code=None,
        project_id=None,
        effective_date=date(2026, 11, 8),
    )

    assert resolved.source_reference_ids == (source.id,)
    assert resolved.standard_reference_ids == (standard.id,)
