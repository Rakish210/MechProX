from decimal import Decimal

import pytest

from mechpro.domain.engineering import Equipment
from mechpro.domain.enums import RevisionState
from mechpro.domain.example import create_natural_gas_reference_model
from mechpro.domain.validation import ModelValidator
from mechpro.engines.gas.workflow import GasApplianceInputError, add_gas_appliance


def test_add_gas_appliance_creates_typed_revision_controlled_object() -> None:
    model = create_natural_gas_reference_model()

    updated = add_gas_appliance(
        model,
        name="Kitchen boiler",
        thermal_input_power_kw=Decimal("60"),
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
        ("", Decimal("10"), "engineer"),
        ("Boiler", Decimal("0"), "engineer"),
        ("Boiler", Decimal("-1"), "engineer"),
        ("Boiler", Decimal("NaN"), "engineer"),
        ("Boiler", Decimal("10"), ""),
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
