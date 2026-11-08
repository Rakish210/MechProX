# Source Traceability

## Source reference model

A SourceReference records:
- Source kind (DWG, DXF, Revit, IFC, PDF, catalogue, standard, manual or other).
- File/document URI and name.
- Document revision and content hash when available.
- Native source entity identifier.
- AutoCAD entity handle, Revit Element UniqueId, PDF page, sheet name or catalogue record as applicable.
- Information-origin classification and capture timestamp.

GeometryReference separately identifies the external geometry representation, file URI, format, native external entity ID, coordinate system and geometry hash. It can point to the SourceReference from which the geometry was obtained.

## Object and property provenance

Each EngineeringObject stores its source-reference IDs, geometry-reference IDs and overall information origin. Each EngineeringProperty independently records its origin and can cite one or more source records and a standard clause.

This distinction matters when a single engineering object combines drawing-imported geometry, a manually entered material specification and an assumption that has not yet been approved.

## Calculation lineage

A CalculationInputSnapshot stores the exact object revision, a frozen list of property snapshots, parameter snapshots and source references. CalculationResult stores the CalculationRun ID and the source engineering objects, parameter codes and standards that support it.

The lineage should be navigable in both directions:
- Result → run → input snapshots → object/property/parameter revisions → source documents.
- Source entity → associated engineering object → networks/systems → affected calculation runs and quantities.

## AI-proposed information

AI must not silently convert a proposal into approved design data. An AI-proposed object or property is recorded as user-reviewable input or an engineering assumption, with the agent/tool run and source context captured. Only an explicit engineering review/approval workflow may mark a revision as approved design.
