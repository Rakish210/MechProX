# MechProX

**Uzman Mekanik Tesisat Mühendisliği Platformu**

MechProX is a Python-first desktop engineering platform. It coordinates one traceable engineering model across deterministic calculations, product and position libraries, CAD/BIM adapters, BOM/BOQ, cost management and technical reporting. AI may interpret, review and orchestrate work; engineering quantities and calculation results must come from traceable model data and validated deterministic methods.

## Current implementation

- PySide6 desktop control-center shell with project navigation.
- Local SQLite project workspace with create, list, update and restore operations.
- Typed Pydantic Common Engineering Data Model (CEDM).
- Lossless JSON serialization and restore of project model snapshots.
- Unit-aware quantities using an offline Pint registry.
- Versioned Parameter Registry with immutable revisions, approval state, source traceability, validity windows and project/jurisdiction/global resolution.
- Global source-document and standard-reference registry with edition, jurisdiction, clause, effective dates, content hashes and source-document links.
- Parameter Registry UI for creating definitions, adding revisions and reviewing revision history.
- Deterministic calculation execution framework with engine registry, declared input context, immutable object/parameter/standard snapshots, reproducible hashes and persisted run outcomes.
- First desktop engineering workflow: add revision-controlled gas appliances and calculate reference volumetric demand using an approved, user-supplied LHV parameter.
- Source provenance, revisions, calculation snapshots and distinct BOM/BOQ contracts.
- Persistent product and BOQ-position catalogues, including versioned many-to-many product/position mappings.
- Engineering Data UI for registering linear elements and equipment with explicit product and optional BOQ mapping assignments.
- Deterministic BOM/BOQ takeoff from project objects: length-based rules (`LENGTH`, `LINEAR_CENTERLINE_LENGTH`) and equipment count (`COUNT`), with unit conversion and source-object traceability.
- Atomic takeoff persistence with stale-project protection and BOQ cost totals grouped by currency.
- Ruff, Pyright, Pytest and Alembic migration workflow.

The current desktop vertical slice supports project creation and local persistence, parameter management, source/standard reference registration, the first gas appliance demand method, product/poz catalogue management, project engineering-object entry, and BOM/BOQ generation for explicitly assigned products and supported measurement rules. The lower heating value must be entered and approved in Parameter Registry before gas demand calculation. Area-, volume- and weight-based takeoff rules, source-document/standard library workflows, advanced BOQ pricing and export, gas pipe-network sizing and pressure-loss calculations, and CAD/BIM operations remain under development.

## Technology baseline

- Python 3.11+
- PySide6 / Qt Widgets
- SQLAlchemy 2 + SQLite + Alembic
- Pydantic 2 and Pint
- Pytest, Ruff and Pyright

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
mechprox
```

Validation:

```powershell
ruff check .
pyright
pytest -q
alembic upgrade head
```

By default, local application data is stored outside the repository in `%USERPROFILE%\\.mechprox`. Set `MECHPROX_DATA_DIR` or `MECHPROX_DATABASE_URL` to override the location.

## Product direction

See [MechProX Product Direction](docs/product/PRODUCT_DIRECTION.md) for the product scope, workflow principles and staged capability roadmap.

## Architecture

- `src/mechprox/core`: application context, configuration and shared services.
- `src/mechprox/domain`: pure, typed engineering domain contracts.
- `src/mechprox/data`: persistence adapters and repositories.
- `src/mechprox/modules`: bounded application modules.
- `src/mechprox/ui`: PySide6 desktop control center.
- `docs/architecture`: architecture decisions and domain documentation.
- `docs/product`: product direction, scope and feature priorities.

The internal Python import namespace remains `mechprox` for source compatibility. The distributed desktop product, installer identity and user-facing application name are MechProX. AutoCAD and Revit remain external desktop applications accessed through bridge adapters. The previously working AutoCAD bridge is to be reused, not recreated as a proof of concept.
