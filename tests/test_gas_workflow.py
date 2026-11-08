from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechpro.calculations import (
    CalculationEngineRegistry,
    CalculationRequest,
    CalculationRunner,
)
from mechpro.data import models  # noqa: F401
from mechpro.data.db import Base
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import ProjectRepository
from mechpro.domain.base import Quantity, QuantityValue
from mechpro.domain.engineering import Equipment
from mechpro.domain.enums import (
    CalculationPurpose,
    CalculationState,
    InformationOrigin,
    RevisionState,
)
from mechpro.domain.example import create_natural_gas_reference_model
from mechpro.domain.validation import ModelValidator
from mechpro.domain.parameters import (
    ParameterDefinition,
    ParameterRevision,
    ParameterRevisionStatus,
    ParameterValueKind,
)
from mechpro.engines.gas.demand import GasApplianceDemandEngine
from mechpro.engines.gas.workflow import GasApplianceInputError, add_gas_appliance


def test_add_gas_appliance_creates_typed_revision_controlled_object() -> None:
    model = create_natural_gas_reference_model()

    updated = add_gas_appliance(
        model,
        name="Kitchen boiler",
        thermal_input_power_kw=Decimal(60),
        changed_by="test-engineer",
    )

    appliance = next(
        item
        for item in updated.objects
        if isinstance(item, Equipment) and item.name == "Kitchen boiler"
    )
    revision = next(item for item in updated.revisions if item.id == appliance.revision_id)

    assert appliance.discipline_code == "GAS"
    assert appliance.equipment_type == "appliance"
    assert revision.object_id == appliance.id
    assert revision.revision_code == "A"
    assert revision.state == RevisionState.DRAFT
    assert ModelValidator().validate(updated).is_valid


@pytest.mark.parametrize(
    "name,power,changed_by",
    [
        ("", Decimal(10), "engineer"),
        ("Boiler", Decimal(0), "engineer"),
        ("Boiler", Decimal(-1), "engineer"),
        ("Boiler", Decimal("NaN"), "engineer"),
        ("Boiler", Decimal(10), ""),
    ],
)
def test_add_gas_appliance_rejects_invalid_inputs(
    name: str,
    power: Decimal,
    changed_by: str,
) -> None:
    model = create_natural_gas_reference_model()

    with pytest.raises(GasApplianceInputError):
        add_gas_appliance(
            model,
            name=name,
            thermal_input_power_kw=power,
            changed_by=changed_by,
        )

def test_new_gas_appliance_can_run_through_the_calculation_framework(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'gas-workflow.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    project_repository = ProjectRepository(factory)
    parameter_repository = ParameterRegistryRepository(factory)

    model = create_natural_gas_reference_model()
    model = add_gas_appliance(
        model,
        name="New boiler",
        thermal_input_power_kw=Decimal(60),
        changed_by="test-engineer",
    )
    project_repository.create(model)

    definition = ParameterDefinition(
        code="GAS.LOWER_HEATING_VALUE",
        name="Natural gas lower heating value",
        discipline_code="GAS",
        category_code="FUEL_PROPERTIES",
        value_kind=ParameterValueKind.QUANTITY,
        expected_dimension="[mass] / [length] / [time] ** 2",
        canonical_unit_code="kilowatt_hour / meter ** 3",
    )
    parameter_repository.register_definition(definition)
    parameter_repository.add_revision(
        ParameterRevision(
            definition_id=definition.id,
            revision_code="TEST-1",
            value=QuantityValue(
                quantity=Quantity(
                    value=Decimal("9.6"),
                    unit_code="kilowatt_hour / meter ** 3",
                )
            ),
            status=ParameterRevisionStatus.APPROVED,
            origin=InformationOrigin.USER_INPUT,
            created_by="test-engineer",
            approved_by="test-approver",
        )
    )

    registry = CalculationEngineRegistry()
    registry.register(GasApplianceDemandEngine())
    runner = CalculationRunner(registry, parameter_repository)
    new_appliance = next(
        item
        for item in model.objects
        if isinstance(item, Equipment) and item.name == "New boiler"
    )
    request = CalculationRequest(
        project_id=model.project.id,
        method_code="GAS.APPLIANCE_DEMAND",
        method_revision="1.0.0",
        input_object_ids=(new_appliance.id,),
        parameter_codes=("GAS.LOWER_HEATING_VALUE",),
        effective_date=date(2026, 11, 8),
        purpose=CalculationPurpose.ENGINEERING,
    )

    execution = runner.run_and_save(model, request, project_repository)

    assert execution.run.state == CalculationState.COMPLETED
    assert len(execution.results) == 2
    total = execution.results[-1].value
    assert isinstance(total, QuantityValue)
    assert total.quantity.value == Decimal("6.25")
    restored = project_repository.get(model.project.id)
    assert restored.calculation_runs[-1].id == execution.run.id
