# Contributor and AI Agent Instructions

Read this file before making changes to MechProX.

## Required project context

1. Read [ROADMAP.md](ROADMAP.md). It is the canonical delivery sequence and status tracker.
2. Read [docs/product/PRODUCT_DIRECTION.md](docs/product/PRODUCT_DIRECTION.md) for the product purpose and non-goals.
3. Read the relevant documents under [docs/architecture/](docs/architecture/) and [docs/engineering/](docs/engineering/) before changing their areas.
4. Inspect the current `main` branch, open pull requests, active branches and working tree before editing. Do not assume an earlier conversation summary is current.

## Product invariants

- MechProX is a full mechanical engineering platform built around one revision-controlled, traceable project model.
- The application is a modular monolith unless an Architecture Decision Record approves a different structure.
- AutoCAD and Revit are real external host applications. Do not implement a fake in-app CAD/BIM substitute.
- Reuse and inspect the previously working AutoCAD bridge. Do not repeat its proof of concept or rewrite it without evidence and approval.
- Keep BOM (physical products/materials) and BOQ (measured contractual work positions) separate.
- Deterministic, testable engineering engines own numeric calculations. AI can prepare inputs, orchestrate tools and review results; it cannot invent or silently approve engineering values.
- All engineering parameters, source data, standards and commercial rates require units, provenance, revision and applicable approval state.
- Treat drawing/document extraction and AI interpretation as proposals until reviewed by an engineer.
- Do not mark a feature complete because a screen, mock, data structure or placeholder exists.

## Implementation workflow

1. Identify the exact roadmap phase and the smallest end-to-end acceptance target.
2. Inspect existing contracts, repositories, migrations, tests and adapters before adding a new abstraction.
3. Write or update an ADR when a significant architectural choice is required.
4. Reuse the single active implementation branch until its acceptance criteria are complete. Do not create a branch per file, commit, small task or module. Keep `main` plus at most one active implementation branch.
5. Implement domain contracts and application use cases before presentation-only work.
6. Keep UI, persistence, external CAD/BIM bridges and AI providers behind typed boundaries.
7. Add unit, integration, migration and regression tests appropriate to the change.
8. Run the repository checks:
   - `ruff check .`
   - `pyright`
   - `pytest -q`
   - `alembic upgrade head`
   - Relevant Qt startup and real-host integration tests.
9. Update the roadmap and related technical documentation in the same pull request.
10. Open one pull request for the completed coherent milestone, describing scope, roadmap phase, design decisions, tests, limitations and any manual verification still required. After merge, remove the completed remote branch; do not leave merged work branches behind.

## Data and safety rules

- Never delete, overwrite or reinterpret existing project data without a migration and preservation test.
- Never silently replace an existing AutoCAD block, layer, entity or user drawing content.
- CAD/BIM write operations require preview/confirmation and a safe rollback/undo path.
- Never seed production engineering values, standards limits, unit prices or product data without a verifiable source and usage rights.
- Never present AI-extracted quantities or classifications as approved design data.
- Preserve calculation snapshots, parameter revisions, standard editions, source references and hashes so historical results remain reproducible.
- Keep local/offline operation available for core workflows. External APIs must be optional and isolated.

## Scope and repository hygiene

- Do not redesign the UI unless the roadmap item requires it; core engineering functionality takes priority.
- Do not create placeholder modules or screens as substitutes for working functionality.
- Avoid unrelated refactoring, bulk formatting and dependency changes.
- Do not include third-party product/site names in user-facing project documentation or runtime labels.
- **Do not modify, rename, replace or delete `logo.jpg`.** Treat it as immutable.
- Do not commit secrets, credentials, generated databases, local settings or machine-specific artifacts.

## Pull request completion checklist

- [ ] The change maps to a named roadmap phase and defined acceptance criteria.
- [ ] Existing behavior and stored project data are preserved.
- [ ] Engineering inputs/outputs have units, validation and provenance where applicable.
- [ ] Tests cover success, invalid inputs, failure handling and relevant regression cases.
- [ ] Static checks and migrations pass.
- [ ] Documentation and roadmap status reflect the actual implementation.
- [ ] No unsupported claim of production readiness or standards compliance is made.
- [ ] `logo.jpg` is unchanged.
