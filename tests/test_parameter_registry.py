from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechpro.data import models  # noqa: F401
from mechpro.data.db import Base
from mechpro.data.parameter_registry_repository import (
    ParameterAlreadyExistsError,
    ParameterRegistryRepository,
)
from mechpro.domain.base import Quantity, QuantityValue
from mechpro.domain.enums import InformationOrigin
from mechpro.domain.parameters import (
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
