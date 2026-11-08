from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechpro.calculations import CalculationEngineRegistry, CalculationRequest, CalculationRunner
from mechpro.data import models  # noqa: F401
from mechpro.data.db import Base
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import ProjectRepository
from mechpro.domain.base import EngineeringProperty, Quantity, QuantityValue
from mechpro.domain.engineering import Equipment
from mechpro.domain.enums import (
    CalculationPurpose,
    CalculationState,
    InformationOrigin,
)
from mechpro.domain.example import create_natural_gas_reference_model
from mechpro.domain.parameters import (
    ParameterDefinition,
    ParameterRevision,
    ParameterRevisionStatus,
    ParameterValueKind,
)
from mechpro.engines.gas.demand import GasApplianceDemandEngine


@pytest.fixture
def gas_services(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'gas-demand.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return ProjectRepository(factory), ParameterRegistryRepository(factory)


@pytest.fixture
def gas_model_and_runner(gas_services):
    project_repository, parameter_repository = gas_services
    model = create_natural_gas_reference_model()
    appliance = next(
        item for item in model.objects if isinstance(item, Equipment) and item.equipment_type == "appliance"
    )
    revised_appliance = appliance.model_copy(
        update={
            "properties": (
                EngineeringProperty(
                    key="thermal_input_power",
                    value=QuantityValue(
                        quantity=Quantity(value=Decimal(60), unit_code="kilowatt")
                    ),
                    origin=InformationOrigin.USER_INPUT,
                ),
            )
        }
    )
    objects = tuple(
        revised_appliance if item.id == appliance.id else item for item in model.objects
    )
    model = model.model_copy(update={"objects": objects})
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
            created_by="test",
            approved_by="test",
        )
    )

    registry = CalculationEngineRegistry()
    registry.register(GasApplianceDemandEngine())
    runner = CalculationRunner(registry, parameter_repository)
    return model, project_repository, runner, appliance


def test_gas_appliance_demand_uses_registry_lhv_and_persists_results(
    gas_model_and_runner,
) -> None:
    model, project_repository, runner, appliance = gas_model_and_runner
    request = CalculationRequest(
        project_id=model.project.id,
        method_code="GAS.APPLIANCE_DEMAND",
        method_revision="1.0.0",
        input_object_ids=(appliance.id,),
        parameter_codes=("GAS.LOWER_HEATING_VALUE",),
        effective_date=date(2026, 11, 8),
        jurisdiction_code="KZ",
        purpose=CalculationPurpose.ENGINEERING,
    )

    execution = runner.run_and_save(model, request, project_repository)
    restored = project_repository.get(model.project.id)

    assert execution.run.state == CalculationState.COMPLETED
    assert len(execution.results) == 2
    total_result = execution.results[-1]
    assert isinstance(total_result.value, QuantityValue)
    assert total_result.value.quantity.value == Decimal("6.25")
    assert total_result.value.quantity.unit_code == "meter ** 3 / hour"
    assert restored.calculation_runs[-1] == execution.run


def test_gas_engine_rejects_missing_appliance_power(gas_services) -> None:
    _, parameter_repository = gas_services
    model = create_natural_gas_reference_model()
    appliance = next(
        item for item in model.objects if isinstance(item, Equipment) and item.equipment_type == "appliance"
    )
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
            created_by="test",
            approved_by="test",
        )
    )
    registry = CalculationEngineRegistry()
    registry.register(GasApplianceDemandEngine())
    runner = CalculationRunner(registry, parameter_repository)
    request = CalculationRequest(
        project_id=model.project.id,
        method_code="GAS.APPLIANCE_DEMAND",
        method_revision="1.0.0",
        input_object_ids=(appliance.id,),
        parameter_codes=("GAS.LOWER_HEATING_VALUE",),
        effective_date=date(2026, 11, 8),
        jurisdiction_code="KZ",
    )

    execution = runner.run(model, request)

    assert execution.run.state == CalculationState.FAILED
    assert execution.run.error_message is not None
    assert "thermal_input_power" in execution.run.error_message
