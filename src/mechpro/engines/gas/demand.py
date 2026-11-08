from decimal import Decimal

from mechpro.calculations.contracts import (
    CalculationContext,
    CalculationEngine,
    CalculationOutput,
    CalculationResultDraft,
)
from mechpro.domain.base import Quantity, QuantityValue
from mechpro.domain.engineering import Equipment
from mechpro.domain.units import UnitService


class GasApplianceDemandEngine(CalculationEngine):
    """Converts appliance thermal input power to reference gas volume flow.

    This method uses the supplied lower heating value. It does not perform
    pressure-loss, pipe-sizing, temperature or pressure-reference corrections.
    """

    method_code = "GAS.APPLIANCE_DEMAND"
    method_revision = "1.0.0"
    engine_name = "MechProX Gas Appliance Demand"
    engine_version = "1.0.0"
    POWER_PROPERTY_KEY = "thermal_input_power"
    LOWER_HEATING_VALUE_PARAMETER = "GAS.LOWER_HEATING_VALUE"
    POWER_UNIT = "kilowatt"
    HEATING_VALUE_UNIT = "kilowatt_hour / meter ** 3"
    FLOW_UNIT = "meter ** 3 / hour"

    @property
    def required_parameter_codes(self) -> tuple[str, ...]:
        return (self.LOWER_HEATING_VALUE_PARAMETER,)

    def __init__(self, unit_service: UnitService | None = None) -> None:
        self._units = unit_service or UnitService()

    def calculate(self, context: CalculationContext) -> CalculationOutput:
        heating_value_revision = context.parameters[self.LOWER_HEATING_VALUE_PARAMETER]
        if not isinstance(heating_value_revision.value, QuantityValue):
            raise TypeError("GAS.LOWER_HEATING_VALUE must be a unit-bearing quantity.")

        heating_value = self._units.convert(
            heating_value_revision.value.quantity,
            self.HEATING_VALUE_UNIT,
        )
        if heating_value.value <= Decimal(0):
            raise ValueError("Lower heating value must be greater than zero.")

        appliance_results: list[CalculationResultDraft] = []
        total_flow = Decimal(0)
        standard_ids = tuple(item.id for item in context.standard_references)

        for item in context.input_objects:
            if not isinstance(item, Equipment) or item.equipment_type != "appliance":
                raise TypeError(
                    f"Calculation input '{item.name}' is not a gas appliance."
                )

            power_properties = [
                prop for prop in item.properties if prop.key == self.POWER_PROPERTY_KEY
            ]
            if len(power_properties) != 1:
                raise ValueError(
                    f"Appliance '{item.name}' must have exactly one "
                    f"'{self.POWER_PROPERTY_KEY}' property."
                )

            property_value = power_properties[0].value
            if not isinstance(property_value, QuantityValue):
                raise TypeError(
                    f"Appliance '{item.name}' thermal input power must be a quantity."
                )

            power = self._units.convert(
                property_value.quantity,
                self.POWER_UNIT,
            )
            if power.value <= Decimal(0):
                raise ValueError(
                    f"Appliance '{item.name}' thermal input power must be greater than zero."
                )

            volume_flow = power.value / heating_value.value
            total_flow += volume_flow
            appliance_results.append(
                CalculationResultDraft(
                    result_code=f"gas.appliance_flow.{item.id}",
                    label=f"{item.name} — reference gas flow",
                    value=QuantityValue(
                        quantity=Quantity(value=volume_flow, unit_code=self.FLOW_UNIT)
                    ),
                    source_object_ids=(item.id,),
                    source_parameter_codes=(self.LOWER_HEATING_VALUE_PARAMETER,),
                    standard_reference_ids=standard_ids,
                )
            )

        appliance_ids = tuple(item.id for item in context.input_objects)
        appliance_results.append(
            CalculationResultDraft(
                result_code="gas.total_reference_flow",
                label="Total reference gas flow",
                value=QuantityValue(
                    quantity=Quantity(value=total_flow, unit_code=self.FLOW_UNIT)
                ),
                source_object_ids=appliance_ids,
                source_parameter_codes=(self.LOWER_HEATING_VALUE_PARAMETER,),
                standard_reference_ids=standard_ids,
            )
        )
        return CalculationOutput(results=tuple(appliance_results))
