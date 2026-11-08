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

## Desktop workflow

1. Create a project in the Project workspace.
2. In Parameter Registry, define `GAS.LOWER_HEATING_VALUE` as a quantity parameter with expected dimension `[mass] / [length] / [time] ** 2` and canonical unit `kilowatt_hour / meter ** 3`.
3. Add an approved parameter revision with its value, scope, effective dates, creator and approver. Record the fuel/reference-condition basis in the revision change summary. The current UI does not yet provide a structured source-document picker; do not treat a free-text note as a verified source link.
4. Open Calculations → Doğalgaz — Cihaz Debisi, select the project and add each appliance with its thermal input power in kW and revision author.
5. Set the effective date and, where relevant, the jurisdiction code. Calculate. All GAS appliance objects in the selected project are included in the total.

## Input contract

- Input objects must be equipment records with `equipment_type = appliance` and discipline `GAS`.
- Every appliance must contain exactly one `thermal_input_power` engineering property.
- The property must be a positive, unit-bearing quantity convertible to kW.
- The `GAS.LOWER_HEATING_VALUE` parameter must resolve to one approved, effective, unit-bearing quantity convertible to kWh/m³.
- The LHV revision must be entered and sourced by the engineering team. The application does not seed or assume a fuel value.
- The LHV and reported flow must use the same stated reference conditions. The current engine documents this requirement but does not yet enforce reference-condition metadata as a typed input.

## Output contract

- One reference flow result per appliance.
- One total reference flow result.
- Results preserve the source appliance IDs, LHV parameter code and any selected standard references.
- Completed and failed runs are retained in the project calculation history. A run is not appended if an input object changed after its snapshot was captured.

## Scope and limitations

This method is an energy-to-volume conversion only. It does not calculate pipe diameter, gas velocity, frictional pressure loss, regulator sizing, diversity factors, pressure/temperature corrections or reference-condition conversions. It is not a complete natural-gas installation design and must not be represented as standards-compliant pipe sizing.
