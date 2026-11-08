# Module Boundaries

## Modules (initial)
- core (data model, registry, validation)
- calc (calculation engines)
- bom_boq (BOM/BOQ generation)
- drawing2d (2D drawing analysis)
- cad_bridge (AutoCAD bridge)
- revit_bridge (Revit bridge)
- bim3d (3D/BIM generation)
- reporting (reports)
- ui (desktop UI)
- ai_orchestration (tool orchestration)

## Rules
- Modules depend on core contracts, not on each other directly.
- No circular dependencies.
- Each module independently testable.
- Plugin registration via entry points / registry.
