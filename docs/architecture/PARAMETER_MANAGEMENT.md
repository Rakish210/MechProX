# Parameter Management

## Policy
- No hardcoded engineering parameters in code.
- Parameters, limits, coefficients, standards, unit prices, specs stored in versioned data sources (DB tables + seed files).
- Calculation algorithms in Python; configurable inputs externalized.
- Validation: schemas, ranges, units, version tags, audit trail.
- Managed via Central Engineering Parameter Registry.
