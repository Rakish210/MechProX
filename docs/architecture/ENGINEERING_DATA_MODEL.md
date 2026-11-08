# Common Engineering Data Model (CEDM) — Version 1

## Purpose

CEDM is the shared, versioned domain contract for the MechProX platform. Engineering modules, drawing adapters, BIM adapters, quantity takeoff, commercial workflows and reports exchange typed records through this model.

The domain package is deliberately independent of PySide6, SQLAlchemy, SQLite, AutoCAD, Revit and AI providers. Persistence and external integrations are adapters around the domain contracts.

## Implemented building blocks

- Project, building, level and space hierarchy.
- Extensible discipline codes and project engineering systems.
- Generic engineering objects plus typed equipment and linear-element records.
- Typed connectors and graph connections. Networks may branch, loop or carry non-flow relationships.
- Source-document/entity traceability and external geometry references.
- Explicit information provenance: user input, drawing import, engineering assumption, calculated data and approved design.
- Standard references, object revisions and approval records.
- Unit-bearing quantities and dimensional validation using an offline unit registry.
- Calculation runs with input snapshots, parameter snapshots, method/engine versions and typed results.
- Separate product/procurement and BOQ position contracts, joined through versioned many-to-many mappings.
- Separate BOM and BOQ documents and line-item records.

## Domain rules

1. Unknown fields are rejected. Engineering properties use typed value variants rather than arbitrary JSON dictionaries.
2. Quantities always carry a unit identifier. Unit conversion is delegated to UnitService; dimensional mismatches are validation errors.
3. A source reference identifies the originating file/document and, when available, its native entity handle, Revit UniqueId, PDF page or catalogue record.
4. Imported geometry is referenced by URI, native identifier and hash. The platform does not replace or mutate CAD/BIM geometry as part of the domain model.
5. A calculation run captures object revisions, property snapshots, parameter revisions, method/engine versions and standard references. Later edits must not rewrite historical inputs.
6. ProductReference and PositionReference are different concepts. A product may map to several BOQ positions and a BOQ position may map to several products.
7. BOM lines identify physical products and procurement quantities. BOQ lines identify commercial positions and measurement-rule versions. They are never merged into one line-item type.

## Quantity and unit policy

Quantity stores a Decimal magnitude and a unit code. Pint supplies offline dimensional checks and unit conversions. A deployment may load additional approved unit definitions. Engineering design coefficients, safety factors, standard limits and calculation assumptions are not part of the unit registry and must be managed separately in the Parameter Registry.

## Scope boundaries

The first CEDM version does not implement engineering equations, design rules, AutoCAD/Revit communication, a 3D geometry kernel, supplier ordering or a live unit-price service. It provides the traceable typed contracts those features will consume.

## Synthetic example

`mechprox.domain.example.create_natural_gas_reference_model()` builds a non-design example with one building, one floor, two spaces, a gas supply source, three connected pipe segments, one gas appliance, source/geometry references, a demonstration calculation record, and separate BOM and BOQ examples. The synthetic quantities and identifiers are not design values or public poz entries.
