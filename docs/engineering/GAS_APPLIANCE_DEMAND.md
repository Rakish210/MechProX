# Gas Appliance Demand — Method 1.0.0

## Purpose

Calculates reference volumetric gas flow from appliance thermal input power and an approved lower heating value (LHV) parameter.

For each appliance:

`Qᵥ = Pᵢₙ / Hᵢ`

where:
- `Qᵥ`: reference gas volume flow, m³/h
- `Pᵢₙ`: appliance thermal input power, kW
- `Hᵢ`: approved lower heating value, kWh/m³

The engine sums individual appliance flows to produce a total reference flow.

## Input contract

- Input objects must be equipment records with `equipment_type = appliance`.
- Every appliance must contain exactly one `thermal_input_power` engineering property.
- The property must be a positive, unit-bearing quantity convertible to kW.
- The `GAS.LOWER_HEATING_VALUE` parameter must resolve to one approved, effective, unit-bearing quantity convertible to kWh/m³.
- The LHV revision must be entered and sourced by the engineering team. The application does not seed or assume a fuel value.

## Output contract

- One reference flow result per appliance.
- One total reference flow result.
- Results preserve the source appliance IDs, LHV parameter code and any selected standard references.

## Scope and limitations

This method is an energy-to-volume conversion only. It does not calculate pipe diameter, gas velocity, frictional pressure loss, regulator sizing, pressure/temperature corrections or diversity factors. The LHV and flow must use the same stated reference conditions. The calculation is not a complete natural-gas installation design and must not be represented as standards-compliant pipe sizing.
