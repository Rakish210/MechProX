# Domain Glossary

| Term | Meaning |
|---|---|
| Project | Top-level engineering work and its controlled model revisions. |
| Building | A physical building within a project. |
| Level | A storey or elevation plane within a building. |
| Space | A room, zone or spatial container within a level. |
| Discipline | An extensible engineering discipline taxonomy entry (for example GAS or VENTILATION). |
| System | A project system within a discipline (for example domestic water or natural gas). |
| Engineering object | A traceable physical or logical design object. |
| Equipment | An engineering object with equipment-specific identity and product reference. |
| Linear element | An engineering object with a physical length (for example a pipe or duct segment). |
| Connector | A typed port belonging to an engineering object. |
| Connection | A graph edge between two object connectors. |
| Network | A collection of member objects and connections. It may branch, loop or represent non-flow relationships. |
| Engineering property | A named typed value with origin, sources and optional standard/revision references. |
| Information origin | The provenance category: user input, drawing import, engineering assumption, calculated or approved design. |
| Source reference | A pointer to an originating file/document and, where possible, a native entity identifier. |
| Geometry reference | A pointer to external DWG/DXF/RVT/IFC/PDF geometry, including source ID and hash. |
| Revision | An immutable identity for a controlled object state. |
| Standard reference | A standard, edition, jurisdiction and clause used by a design or calculation. |
| Calculation run | A reproducible execution record tied to method, engine, inputs, parameters and standards. |
| Calculation snapshot | Frozen source-object property and parameter values captured for a run. |
| Product reference | A physical product/material catalogue record. |
| Position reference | A commercial BOQ/poz catalogue record. |
| Position-product mapping | A versioned relation connecting a BOQ position to a physical product and measurement rule. |
| BOM | Physical product/material takeoff for procurement. |
| BOQ | Commercial work-position quantity measurement. |

## Abbreviations

- CEDM: Common Engineering Data Model
- BOM: Bill of Materials
- BOQ: Bill of Quantities
- IFC: Industry Foundation Classes
- DWG/DXF: AutoCAD drawing/exchange formats
- UniqueId: Revit persistent element identifier
