# Initial Roadmap — MechProX

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
- Public-works position (poz), unit-price and analysis catalogues with source, license and revision tracking.
- Custom company/project catalogues and reusable analysis templates.
- Status: Parameter Registry persistence, deterministic global/jurisdiction/project resolution and initial desktop management UI implemented. Standards/product/poz ingestion remains open.

## Phase 4 — Deterministic engineering core
- Calculation contracts, validation framework and reproducible calculation runs.
- Searchable Engineering Method Catalogue grouped by discipline and purpose.
- Each method has a revision, declared units, input/output contract, standards/parameter references, limitations and independent regression cases.
- Natural-gas network design: appliance demand, network connectivity, load aggregation, pipe sizing, velocity and pressure-loss calculations.
- Independent reference calculations, standards traceability and reproducible reports.
- No AI-generated numeric engineering results; AI orchestrates deterministic tools only.
- Status: calculation engine registry and reproducible execution framework implemented. Gas appliance demand method v1.0.0 and its first desktop workflow are implemented. Network sizing, velocity, pressure loss, regulator calculations and typed reference-condition enforcement remain open.

## Phase 5 — Drawing analysis and AutoCAD integration
- PDF/DWG drawing-set ingestion, sheet indexing and source fingerprints.
- Reuse the previously working AutoCAD bridge; do not repeat its PoC or rewrite it.
- Map drawing entities to the Common Engineering Data Model and keep handles/source references.
- Reusable block, layer and discipline drawing-style libraries.
- Controlled round-trip updates, drawing-model reconciliation and revision comparison.

## Phase 6 — BOM, BOQ and commercial workflows
- BOM derived from physical products/materials and quantities.
- BOQ derived from position mappings and measurement rules; many-to-many mapping stays explicit.
- Measurement sheets with work groups, sections, formulas, deductions and subtotals.
- Material/labour/equipment/transport analyses, custom positions, supplier alternatives and unit-price history.
- Cost estimates, procurement lists, quotation comparison and staged progress-payment/final-account workflows.
- Traceability from every quantity and rate to source objects, catalog revisions and mapping rules.

## Phase 7 — Revit, IFC and coordinated BIM
- Revit bridge and native MEP element generation.
- 3D routing, fittings, equipment placement and model validation.
- IFC exchange and model/property validation.
- Clash and spatial coordination.

## Phase 8 — AI orchestration and drawing intelligence
- Provider-independent interface for local and optional cloud models.
- Tool catalogue with strict schemas and permission boundaries.
- AI-assisted extraction proposals from drawings, schedules and specifications with source overlays and approval.
- Scope verification, missing/duplicate/conflicting-item review and numbered RFI drafts.
- Revision delta analysis and controlled model-change proposals.
- Deterministic workflow state machine; AI selects and coordinates tools but does not replace calculation engines.
- Context filtering, caching, token/cost accounting and model capability benchmarks.

## Phase 9 — Technical reporting and delivery packages
- Calculation reports with source inputs, methods, standards, parameter revisions and limitations.
- Drawing/model schedules, BOM, BOQ, cost summaries, specifications and procurement reports.
- Review/approval workflow, revision comparison and authority-submission packages.
- Excel/CSV and defined external estimating-system exports.

## Phase 10 — Additional disciplines and optimization
- Plumbing, heating, cooling, ventilation, fire protection, compressed air, medical gas and other mechanical disciplines.
- Multi-discipline coordination, design alternatives and constrained optimization.
