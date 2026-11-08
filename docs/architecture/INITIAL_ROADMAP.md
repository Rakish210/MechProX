# Initial Roadmap

## Phase 0 — Architecture discovery
- Repository audit, architecture baseline and initial ADRs.
- Status: completed.

## Phase 1 — Core application foundation
- Python/PySide6 desktop control center.
- SQLite/SQLAlchemy/Alembic persistence, configuration and logging.
- CI, linting, type checking and tests.
- Project workspace: create, list, update and restore typed project snapshots.
- Status: foundation and first usable project-management vertical slice implemented.

## Phase 2 — Common Engineering Data Model
- Typed, versioned domain contracts.
- Project/building/level/space hierarchy.
- Disciplines, systems, networks, connectors, components and connections.
- Explicit source traceability, provenance, revisions and calculation snapshots.
- Separate product/procurement and BOQ position concepts.
- Status: CEDM v1 contracts, serialization and validation implemented. The synthetic gas model is test data only, not an engineering calculation.

## Phase 3 — Engineering knowledge and libraries
- Parameter Registry with typed definitions and immutable revisions.
- Approval state, provenance, standards references, effective dates and scope resolution.
- Standards, editions, clauses, jurisdiction and effective dates.
- Product, manufacturer, fitting, equipment and Revit-family references.
- Public-works position (poz) and unit-price catalogues with source/revision tracking.
- Status: Parameter Registry persistence, deterministic global/jurisdiction/project resolution and initial desktop management UI implemented. Standards/product/poz ingestion remains open.

## Phase 4 — Deterministic engineering core
- Calculation contracts, validation framework and reproducible calculation runs.
- First complete discipline workflow: natural gas.
- Independent reference calculations, standards traceability and regression tests.
- No AI-generated numeric engineering results; AI orchestrates deterministic tools only.
- Status: calculation engine registry, explicit request/context contracts, revision-gated input capture, full object/parameter/standard snapshots, deterministic input/output hashes, result provenance and persisted failed/completed runs implemented. Gas appliance demand method v1.0.0 and its first desktop workflow are implemented. The user can add revision-controlled appliances, resolve an approved LHV parameter and persist reference-flow results. Gas pipe sizing, velocity, pressure loss, regulator calculations and typed reference-condition enforcement remain open.

## Phase 5 — Drawing analysis and AutoCAD integration
- 2D drawing ingestion and entity/source mapping.
- Reuse the previously working AutoCAD bridge; do not repeat its PoC or rewrite it.
- Map drawing entities to the Common Engineering Data Model.
- Support controlled round-trip updates.

## Phase 6 — BOM, BOQ and commercial workflows
- BOM derived from physical products/materials and quantities.
- BOQ derived from position mappings and measurement rules.
- Procurement lists, supplier/product alternatives, unit prices and cost summaries.
- Traceability from every quantity to its source objects and mapping rules.

## Phase 7 — Revit, IFC and coordinated BIM
- Revit bridge and native MEP element generation.
- 3D routing, fittings, equipment placement and model validation.
- IFC exchange and model/property validation.
- Clash and spatial coordination.

## Phase 8 — AI orchestration
- Provider-independent interface for local and optional cloud models.
- Tool catalogue with strict schemas and permission boundaries.
- Deterministic workflow state machine; AI selects and coordinates tools but does not replace calculation engines.
- Context filtering, caching, token/cost accounting and model capability benchmarks.

## Phase 9 — Technical reporting and delivery packages
- Calculation reports with source inputs, methods, standards and revisions.
- Drawing/model schedules, BOM, BOQ, specifications and procurement reports.
- Review/approval workflow, revision comparison and authority-submission packages.

## Phase 10 — Additional disciplines and optimization
- Plumbing, heating, cooling, ventilation, fire protection and other mechanical disciplines.
- Multi-discipline coordination, design alternatives and constrained optimization.
