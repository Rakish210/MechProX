# MechProX — Product & Engineering Roadmap

**Status:** Active delivery roadmap  
**Version:** 1.0  
**Last reviewed:** 2026-11-08  
**Canonical source:** This file defines delivery order and phase status. The product vision remains in [docs/product/PRODUCT_DIRECTION.md](docs/product/PRODUCT_DIRECTION.md); architecture contracts and decisions remain in [docs/architecture/](docs/architecture/).

> MechProX is intended to become a complete AI-assisted mechanical engineering platform built around one traceable engineering model. It is not a CAD block library, a collection of disconnected calculators, or a chatbot. AI may interpret, plan, coordinate and review; engineering calculations and approved quantities must come from deterministic, testable methods and validated project data.

## 1. Delivery rules

1. **One shared engineering model.** Drawings, systems, equipment, calculations, products, BOM, BOQ, cost records and reports must refer to the same revision-controlled project model.
2. **Deterministic engineering.** No AI-generated diameter, pressure, flow, heat load, quantity, price or compliance conclusion may be silently accepted as an engineering result. Such values must be calculated or resolved from approved, traceable data.
3. **Evidence and approval.** Imported or AI-extracted information is a proposal until reviewed. Preserve source file, sheet/page, entity/handle, model revision, standard edition/clause and approval state wherever applicable.
4. **Native CAD/BIM applications.** AutoCAD and Revit remain real external applications. Do not substitute an imitation drawing canvas for their native capabilities.
5. **BOM and BOQ remain separate.** BOM describes physical products/materials. BOQ describes measured contractual work positions. Their mapping is explicit, versioned and auditable.
6. **Vertical slices, not disconnected screens.** A phase is complete only when its workflow works end-to-end and has appropriate tests and engineering validation.
7. **Local-first.** Core project work must remain usable offline. External AI services, if enabled, are optional providers rather than hard dependencies.
8. **Incremental architecture.** Keep the initial application as a modular monolith with typed module boundaries. Do not introduce distributed services without a demonstrated need.

## 2. Verified repository baseline

Baseline inspected against `main` at commit `4bf1c05464ca0e8d876a3d666357f2dac4c0b191` on 2026-11-08.

| Capability | Verified state | Remaining gap |
|---|---|---|
| Desktop application | PySide6 desktop shell and project workflows exist | UI is a control center, not yet the complete design workspace |
| Persistence | SQLite, SQLAlchemy, Alembic and project snapshot persistence exist | Production backup, recovery, portability and upgrade tests need a defined policy |
| Common Engineering Data Model | Typed project/building/level/space, engineering object, connector/network, quantity, provenance and revision contracts exist | Model coverage and invariants must be hardened against real projects and discipline workflows |
| Parameter and source registry | Versioned parameter definitions/revisions, source documents and standard/clause references exist | Document ingestion, evidence storage, authoritative datasets and richer review workflows remain |
| Calculation framework | Deterministic engine registry/runner, input snapshots, source/standard snapshots and hashes exist | Method catalogue, output schemas, cancellation/progress, comparison and discipline engines remain |
| Natural gas | Appliance demand from thermal input and approved LHV has a deterministic engine and desktop workflow | No network load aggregation, pipe sizing, velocity, pressure loss, regulator design or complete gas report |
| Product and position catalogues | Persistent products, BOQ positions and versioned many-to-many mappings exist | Full catalog ingestion, licensing/provenance, richer assemblies and commercial analysis remain |
| BOM / BOQ | Basic takeoff from explicitly assigned engineering objects supports length and count rules | No complete measurement-sheet system, advanced deductions/areas/volumes/weights, full cost build-up or native CAD-derived quantity reconciliation |
| AutoCAD | Earlier working bridge is reported by the product owner; AutoCAD 2021 / .NET Framework 4.8 is the recorded compatibility context | The bridge source/artifact is not in the current repository tree; it must be located and reused, not replaced by another proof of concept |
| Revit / IFC | Architecture direction is documented | No working Revit/IFC adapter or native MEP element generation is present |
| AI orchestration | Product principles and intended tool boundaries are documented | No implemented provider-independent agent/tool gateway or production agent workflow is present |
| Drawing intelligence | Source-reference contracts exist | No complete DWG/DXF/PDF ingestion, architectural interpretation or drawing-to-model reconciliation workflow exists |

The source/standard snapshot work is present in `main`. The separate `feature/traceable-calculation-snapshots` branch has diverged from `main`; do not merge, rebase or delete it blindly. Inspect its history and differences first. The logo asset `logo.jpg` is a protected project asset and must not be modified.

## 3. Current focus — Phase 0: Architecture baseline

**Current status: In progress.**

**Objective:** establish one accurate architecture and code baseline before adding another isolated feature.

- [x] Inspect current `main`, product direction and key architecture documents.
- [x] Verify the current CEDM, calculation runner, source/standard snapshots, gas demand workflow and basic BOM/BOQ implementation.
- [x] Verify that the AutoCAD bridge source is absent from the current repository tree and record the previously reported compatibility context.
- [ ] Complete a file-level audit of application, domain, persistence, UI, calculation and test boundaries.
- [ ] Review migrations, test coverage, CI outcomes and the outstanding divergent feature branch.
- [ ] Identify model invariants, duplicated responsibilities, incomplete contracts and persistence/recovery risks.
- [ ] Publish or update Architecture Decision Records for unresolved high-impact decisions.
- [ ] Produce a prioritized gap list linked to roadmap work items.

**Exit criteria:** a code-backed inventory of what exists, a documented target boundary for each subsystem, no unresolved ambiguity about the next implementation task, and an agreed first vertical slice. No broad UI redesign or new discipline module is part of this phase.

## 4. Product delivery phases

### Phase 1 — Harden the shared engineering platform

**Status:** Partially implemented; next after Phase 0.

- Complete CEDM contracts for project, building, levels, spaces, systems, networks, connectors, equipment, terminals, linear elements, fittings, properties, geometry and source references.
- Define and enforce graph/network invariants, ownership, connection compatibility, dimensional validation and revision rules.
- Complete the application-service boundary so UI, command-line workflows, AI tools and CAD/BIM adapters use the same use cases.
- Make data migrations additive and test upgrades from real earlier project snapshots.
- Define project backup, restore, export/import, portability and recovery verification. A working restore button alone is not a complete backup policy.
- Preserve immutable calculation inputs, parameter revisions, sources, standard editions and method versions.
- Add audit history and explicit review/approval transitions for assumptions, imported observations and proposed design changes.
- Document module dependencies and prohibit circular dependencies.

**Exit criteria:** a real project can be created, revised, backed up, restored and reopened without loss of object identity, provenance or calculation history; domain and persistence tests verify the invariants.

### Phase 2 — Recover and integrate the existing AutoCAD bridge

**Status:** Blocked on locating the previously working source/artifact; architecture is documented.

- Locate the existing bridge source project or compiled artifact and its actual communication protocol.
- Preserve the recorded AutoCAD 2021 / .NET Framework 4.8 compatibility unless inspection proves otherwise.
- Do not rebuild a second proof of concept or replace the bridge without a documented technical reason and product-owner agreement.
- Build a versioned Python-side adapter around the real protocol; keep engineering rules and calculations outside the AutoCAD plug-in.
- Verify attach/open, drawing identity, read-only entity inspection, native handle mapping, metadata exchange, controlled entity creation/update and structured error handling.
- Implement preview/confirmation, transaction boundaries, undo/rollback and collision protection before allowing bulk changes.
- Verify behavior against a real AutoCAD installation, not a mock alone.

**Exit criteria:** a supported test drawing can be inspected and safely modified through the existing bridge, with source handles preserved and changes reversible. Evidence includes a repeatable integration test procedure.

### Phase 3 — Deterministic natural-gas network engineering

**Status:** Appliance-demand method exists; network design is not implemented.

This is the **proposed first engineering discipline for the initial end-to-end product slice**, because a gas appliance demand workflow already exists. It is a first delivery target, not a limit on the platform's eventual scope.

- Define gas network topology: supply/source, regulators, branches, nodes, pipe sections, appliance endpoints and connection rules.
- Define approved gas properties, reference conditions, pressure stages, material/roughness data and applicable jurisdiction/standard rule packs.
- Implement load aggregation and any diversity/simultaneity rules as explicit, sourced parameters and deterministic methods.
- Implement pipe diameter selection, flow velocity, frictional and local pressure losses, regulator/stage checks and critical-path evaluation as separately testable methods.
- Validate physical dimensions, pressure basis, reference temperature/pressure and input completeness before calculations.
- Return segment-level and network-level results, warnings, limiting paths and calculation provenance.
- Build independent reference cases and regression tests, including hand-checked examples.
- Do not encode unverified engineering values as defaults. Every design limit, coefficient and material property needs a source, revision and approval state.

**Exit criteria:** the engine calculates a complete defined gas network from approved inputs, reports each segment and the critical path, flags violated criteria, reproduces identical results from identical snapshots and passes independent reference cases.

### Phase 4 — First complete engineering workflow (MechProX V1 candidate)

**Status:** Planned; depends on Phases 1–3.

Deliver one useful project workflow rather than several unrelated feature pages:

1. Create/open a project and attach an architectural drawing in the native AutoCAD environment.
2. Identify or enter the relevant spaces, supply point, gas appliances and capacities; preserve the drawing references.
3. Let the engineer confirm missing or uncertain design inputs, standards, fuel/reference conditions and route.
4. Build or review the connected gas network in the engineering model.
5. Run the deterministic network calculations and present traceable results and warnings.
6. Apply approved drawing changes through the real AutoCAD bridge.
7. Generate distinct BOM and BOQ outputs from approved model objects and measurement mappings.
8. Produce a technical calculation report with inputs, assumptions, standards, parameter revisions, method version, warnings and output hashes.
9. Provide a project cost summary using explicitly sourced/revisioned rates where available.

**Exit criteria:** a sample project completes the entire workflow from design input to calculation, native drawing update, BOM, BOQ and report. The drawing, calculations and quantities reconcile to the same project-model revisions. A reviewer can trace every critical value back to its source.

### Phase 5 — Commercial and quantity-surveying workflows

**Status:** Basic BOM/BOQ foundation exists; full commercial workflows are planned.

- Expand measurement rules to count, length, centerline length, area, volume, weight, assemblies and discipline-specific formulas.
- Add measurement sheets with work groups, sections, formula inputs, deductions, subtotals and revision history.
- Support product-to-position mappings, assemblies and many-to-many consumption rules with effective revisions.
- Add unit-rate analysis for material, labour, equipment, transport, waste, overhead and other jurisdiction-specific components.
- Support custom company/project positions, alternative products, supplier quotations and price history.
- Add estimates, procurement exports, progress-payment and final-account workflows as separately scoped modules.
- Keep source agency, publication date, jurisdiction, licence/usage terms and data revision with imported catalogue data.

**Exit criteria:** BOM quantities reconcile with approved physical model objects; BOQ quantities reconcile with approved measurement rules; rates and totals are reproducible and auditable.

### Phase 6 — Drawing and architectural intelligence

**Status:** Planned; no complete ingestion pipeline is present.

- Ingest DWG/DXF/PDF drawing sets with fingerprints, sheet indexes, units, scale, coordinate system and native entity references.
- Read layers, blocks, geometry and supported entity attributes without destroying source drawings.
- Identify or propose building outlines, levels, rooms/spaces, walls, doors, windows, shafts and relevant architectural constraints.
- Classify building use, occupancy, hazard and fire-safety attributes only through an evidence-backed rules workflow; request engineer confirmation when information is uncertain or safety-critical.
- Reconcile drawing observations with the CEDM to identify missing, duplicate, conflicting or disconnected objects.
- Compare drawing revisions and generate traceable change sets.
- Produce draft RFIs tied to the exact sheet, detail, specification clause or model object.
- Treat AI/vision output as proposed observations with source overlays and accept/reject/edit controls, never as certified quantities or approved design.

**Exit criteria:** an imported drawing set can be traced to a reviewable building/space model, with source references and a documented confidence/approval state for every extracted observation.

### Phase 7 — Additional mechanical disciplines

**Status:** Planned. Each discipline must be a validated vertical slice, not just a UI module.

Recommended implementation order, subject to dependency and engineering review:

1. **Sıhhi tesisat, vitrifiye ve su sistemleri:** cold/hot water demand, pressure zones, pipe sizing, pressure loss, drainage and vent systems.
2. **Isıtma, kazanlar ve hidronik sistemler:** heat-loss inputs, heating loads, emitters, pipe sizing, pumps, balancing and boiler/plant selection.
3. **Soğutma ve iklimlendirme:** cooling loads, chilled-water/refrigerant networks, equipment selection and condensate drainage.
4. **Havalandırma:** fresh-air/exhaust requirements, duct sizing, velocity, pressure loss, fans and air balancing.
5. **Yangın tesisatı ve yangın güvenliği:** hazard classification with code evidence, hydrants, hose cabinets, sprinklers, pump duties, hydraulic critical circuits, smoke extraction and pressurization.
6. **Isı pompaları, mutfak/soğutma ve özel tesisatlar:** equipment integration and applicable system-specific methods.
7. **Diğer mühendislik alanları:** compressed air, medical gas and future approved disciplines.

For every discipline: define inputs and assumptions, method codes/revisions, standards/rule packs, unit contracts, reference cases, warnings, outputs, object relationships, CAD mapping and BOM/BOQ rules.

**Exit criteria:** a discipline is called production-ready only after end-to-end workflow tests, independent engineering validation and traceable drawing/quantity/report output.

### Phase 8 — Revit, IFC and coordinated BIM

**Status:** Architecture direction only; no working adapter is present.

- Choose and document the Revit add-in hosting and Python-to-Revit communication contract.
- Create editable native Revit MEP elements (pipes, ducts, fittings, terminals, equipment and families) rather than generic unconnected solids.
- Map CEDM object IDs and revisions to native Revit UniqueIds and geometry references.
- Support coordinate systems, levels, connectors, system classification and transaction/rollback.
- Add IFC import/export and property/geometry validation.
- Implement 3D routing, spatial constraints, model QA and clash/coordination workflows.
- Keep 2D drawing and 3D BIM linked to the same engineering model.

**Exit criteria:** approved CEDM changes create/update native, editable Revit MEP elements; source IDs and revisions survive round trips; model validation and clash reports are reproducible.

### Phase 9 — AI orchestration and engineering agent

**Status:** Product principles documented; production implementation not present.

- Implement provider-independent model adapters for supported local and optional cloud models.
- Expose strict, typed tools for project inspection, drawing observations, parameter/source lookup, deterministic calculations, validation, CAD/BIM changes, BOM/BOQ generation and reporting.
- Apply least-privilege access, explicit user approval for consequential changes, idempotency, timeouts, structured errors and audit logs.
- Give the agent only the context required for each tool call; do not provide unrestricted database or filesystem access.
- Let AI plan tasks, ask for missing inputs, invoke approved tools, interpret deterministic results and prepare review proposals.
- Add project/document understanding, design coordination, scope checks, discrepancy detection and RFI drafting.
- Measure tool-call correctness, task completion, invalid-action rate, reproducibility, latency and local hardware requirements.

**Exit criteria:** the agent can complete a defined engineering workflow through tools, cannot bypass deterministic validation or approval gates, and every action/result is auditable.

### Phase 10 — Production delivery and operations

**Status:** Planned.

- Offline-capable installer and upgrade path for supported Windows environments.
- Backup/restore verification, project portability and recovery exercises.
- Logging, diagnostic bundles, data migration checks and performance profiling on large drawings/projects.
- Security review for local files, optional AI credentials and external bridge communication.
- Regression, integration and acceptance test suites for each supported AutoCAD/Revit version.
- Technical reports, project handover, revision comparisons and release documentation.
- Usability and visual-design refinement after core workflows have proven stable.

**Exit criteria:** a reproducible installation and upgrade can open, calculate, modify and export a project without data loss, and support teams can diagnose failures from logs and test evidence.

## 5. Engineering completion gates

A calculation method is not complete until it has:

- Stable method code and method revision.
- Explicit input/output schemas, dimensional units and applicability constraints.
- Documented assumptions, equations/algorithm and limitations.
- Versioned parameter data and standard editions/clauses where relevant.
- Independent reference cases, hand checks and automated regression tests.
- Input snapshots, source provenance, output hashes and reproducible historical runs.
- Clear warnings/errors for missing, invalid or out-of-scope inputs.

A CAD/BIM integration is not complete until it has:

- Real-host integration tests, not mock-only tests.
- Stable identifiers and drawing/model fingerprints.
- Preview/approval, safe transactions, rollback/undo and conflict handling.
- Round-trip and revision tests that protect existing user content.

A quantity/commercial feature is not complete until it has:

- A declared measurement rule and version.
- Traceability to model objects or drawing entities.
- Independent quantity checks and unit validation.
- Distinct BOM/BOQ semantics and revisioned product/position mappings.
- Source and rate provenance for issued cost outputs.

## 6. Collaboration protocol for developers and AI agents

All contributors must read [AGENTS.md](AGENTS.md) before changing code. The following rules are mandatory:

- Start from the current `main`; inspect open branches and existing work before creating a new branch.
- Read this roadmap, [PRODUCT_DIRECTION.md](docs/product/PRODUCT_DIRECTION.md), and the relevant architecture/method documents before implementation.
- Work on a focused feature branch and submit a pull request. Do not push directly to `main`.
- State the roadmap phase and acceptance criteria in the issue/PR description.
- Make the smallest coherent vertical change. Do not expand scope or introduce a new subsystem just because it is technically interesting.
- Add tests and update the roadmap status only when the acceptance criteria are met in code and verified.
- Never claim AutoCAD, Revit, standards compliance, engineering correctness or end-to-end operation based only on mocks, UI screens or unverified calculations.
- Preserve existing project data, migrations, public contracts and user drawing content.
- Do not modify `logo.jpg`.
- If implementation order, scope or a product decision needs to change, record the reason and update this roadmap/ADR rather than silently changing direction.

## 7. Roadmap maintenance

- Update this file in the same pull request that completes or materially changes a roadmap item.
- Use the status labels **Not started**, **In progress**, **Blocked**, **Partially implemented** and **Done** consistently.
- Mark an item **Done** only when its acceptance criteria are satisfied and relevant checks pass.
- Record major architectural changes in `docs/architecture/adr/`.
- Keep the product vision in `docs/product/PRODUCT_DIRECTION.md`; this roadmap controls sequencing and progress.
- Review priorities after each end-to-end milestone. Dates are intentionally not promised until scope and dependencies are validated.
