# Initial Roadmap

## Phase 0 — Architecture discovery
- Repository audit, architecture baseline and initial ADRs.
- Status: completed.

## Phase 1 — Core application foundation
- Python/PySide6 desktop shell.
- Basic module registry, configuration, logging and SQLite/SQLAlchemy/Alembic foundation.
- CI, linting, type checking and initial tests.
- Status: initial foundation pushed; repository hygiene and Qt startup coverage added on the maintenance branch.

## Phase 2 — Common Engineering Data Model
- Typed, versioned domain contracts.
- Project/building/level/space hierarchy.
- Disciplines, systems, networks, connectors, components and connections.
- Explicit source traceability, provenance, revisions and calculation snapshots.
- Separate product/procurement and BOQ position concepts.
- Status: first implementation in progress on `phase-2/engineering-data-model`.

## Phase 3 — Engineering knowledge and libraries
- Parameter Registry and unit-aware values.
- Standards, editions, clauses, jurisdiction and effective dates.
- Calculation-method definitions and design criteria.
- Product, manufacturer, fitting, equipment and Revit-family references.
- Public-works position (poz) and unit-price catalogues with source/revision tracking.

## Phase 4 — Deterministic engineering core
- Calculation contracts, validation framework and reproducible calculation runs.
- First complete discipline workflow, preferably natural gas.
- Independent reference calculations and regression tests.

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
