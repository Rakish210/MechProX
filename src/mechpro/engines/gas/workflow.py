from decimal import Decimal
from uuid import uuid4

from mechpro.domain.base import EngineeringProperty, Quantity, QuantityValue, Revision
from mechpro.domain.engineering import Equipment
from mechpro.domain.enums import InformationOrigin, RevisionState
from mechpro.domain.model import EngineeringModel
from mechpro.domain.project import Discipline
from mechpro.domain.validation import ModelValidator


class GasApplianceInputError(ValueError):
    """Raised when a gas appliance cannot be added to the engineering model."""


def add_gas_appliance(
    model: EngineeringModel,
    *,
    name: str,
    thermal_input_power_kw: Decimal,
    changed_by: str,
) -> EngineeringModel:
    """Add a revision-controlled gas appliance to a project model."""
    normalized_name = name.strip()
    if not normalized_name:
        raise GasApplianceInputError("Appliance name is required.")
    if not thermal_input_power_kw.is_finite() or thermal_input_power_kw <= 0:
        raise GasApplianceInputError("Thermal input power must be a finite value greater than zero.")
    if not changed_by.strip():
        raise GasApplianceInputError("A creator identity is required for the object revision.")

    gas_disciplines = tuple(
        item for item in model.disciplines if item.code == "GAS"
    )
    if len(gas_disciplines) > 1:
        raise GasApplianceInputError(
            "The project contains duplicate GAS discipline definitions; resolve them before adding equipment."
        )

    appliance_id = uuid4()
    revision = Revision(
        object_id=appliance_id,
        revision_code="A",
        state=RevisionState.DRAFT,
        changed_by=changed_by.strip(),
        change_summary="Initial gas appliance record created in MechPro.",
    )
    appliance = Equipment(
        id=appliance_id,
        project_id=model.project.id,
        name=normalized_name,
        category_code="gas_appliance",
        discipline_code="GAS",
        equipment_type="appliance",
        information_origin=InformationOrigin.USER_INPUT,
        revision_id=revision.id,
        properties=(
            EngineeringProperty(
                key="thermal_input_power",
                value=QuantityValue(
                    quantity=Quantity(
                        value=thermal_input_power_kw,
                        unit_code="kilowatt",
                    )
                ),
                origin=InformationOrigin.USER_INPUT,
                revision_id=revision.id,
                note="Appliance rated thermal input power entered by the user.",
            ),
        ),
    )
    updated_model = model.model_copy(
        update={
            "disciplines": (
                model.disciplines
                if gas_disciplines
                else (*model.disciplines, Discipline(code="GAS", name="Doğalgaz"))
            ),
            "revisions": (*model.revisions, revision),
            "objects": (*model.objects, appliance),
        }
    )
    ModelValidator().validate(updated_model).raise_for_errors()
    return updated_model
