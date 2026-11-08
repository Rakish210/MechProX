from decimal import Decimal

import pytest
from pydantic import ValidationError

from mechpro.domain.base import Quantity
from mechpro.domain.example import create_natural_gas_reference_model
from mechpro.domain.serialization import deserialize_model, serialize_model
from mechpro.domain.units import UnitService, UnitValidationError
from mechpro.domain.validation import ModelValidator


def test_synthetic_reference_model_is_valid() -> None:
    model = create_natural_gas_reference_model()
    report = ModelValidator().validate(model)

    assert report.is_valid, report.issues
    assert len(model.objects) == 5
    assert len(model.networks) == 1
    assert len(model.connections) == 4
    assert len(model.networks[0].member_object_ids) == 5


def test_model_json_round_trip_preserves_typed_records() -> None:
    original = create_natural_gas_reference_model()

    restored = deserialize_model(serialize_model(original))

    assert restored == original
    assert restored.objects[1].kind == "linear_element"
    assert restored.calculation_runs[0].purpose.value == "demonstration"


def test_network_rejects_missing_connector_reference() -> None:
    model = create_natural_gas_reference_model()
    broken_connection = model.connections[0].model_copy(
        update={
            "from_endpoint": model.connections[0].from_endpoint.model_copy(
                update={"connector_id": model.connections[0].id}
            )
        }
    )
    broken = model.model_copy(
        update={"connections": (broken_connection, *model.connections[1:])}
    )

    report = ModelValidator().validate(broken)

    assert not report.is_valid
    assert any(issue.code == "connection_connector_missing" for issue in report.issues)


def test_quantity_unit_conversion_and_dimension_validation() -> None:
    units = UnitService()
    converted = units.convert(
        Quantity(value=Decimal("2.5"), unit_code="meter"),
        "millimeter",
    )

    assert converted.value == Decimal("2500.0")
    units.validate(converted, expected_dimension="[length]")


def test_incompatible_quantity_dimension_is_rejected() -> None:
    units = UnitService()

    with pytest.raises(UnitValidationError):
        units.validate(
            Quantity(value=Decimal(2), unit_code="second"),
            expected_dimension="[length]",
        )


def test_unknown_unit_is_rejected() -> None:
    with pytest.raises(UnitValidationError):
        UnitService().validate(
            Quantity(value=Decimal(1), unit_code="unknown_engineering_unit")
        )


def test_domain_contract_rejects_unstructured_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Quantity(value=Decimal(2), unit_code="meter", arbitrary_engineering_data={})


def test_bom_and_boq_are_distinct_domain_records() -> None:
    model = create_natural_gas_reference_model()

    assert len(model.bom_documents) == 1
    assert len(model.boq_documents) == 1
    assert model.bom_documents[0].items[0].product_reference_id != model.boq_documents[0].items[0].position_reference_id
    assert model.boq_documents[0].items[0].mapping_id == model.position_product_mappings[0].id


def test_boq_unit_must_match_position_dimension() -> None:
    model = create_natural_gas_reference_model()
    original_document = model.boq_documents[0]
    original_item = original_document.items[0]
    invalid_item = original_item.model_copy(
        update={"quantity": Quantity(value=Decimal("13"), unit_code="second")}
    )
    invalid_document = original_document.model_copy(update={"items": (invalid_item,)})
    invalid_model = model.model_copy(update={"boq_documents": (invalid_document,)})

    report = ModelValidator().validate(invalid_model)

    assert any(issue.code == "boq_unit_mismatch" for issue in report.issues)


def test_calculation_result_must_reference_captured_input_objects() -> None:
    model = create_natural_gas_reference_model()
    result = model.calculation_results[0].model_copy(
        update={"source_object_ids": (model.objects[-1].id,)}
    )
    invalid_model = model.model_copy(update={"calculation_results": (result,)})

    report = ModelValidator().validate(invalid_model)

    assert any(issue.code == "result_source_not_captured" for issue in report.issues)
