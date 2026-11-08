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
- Parameter Registry UI for creating definitions, adding revisions and reviewing revision history.
- Deterministic calculation execution framework with engine registry, declared input context, immutable object/parameter/standard snapshots, reproducible hashes and persisted run outcomes.
- First desktop engineering workflow: add revision-controlled gas appliances and calculate reference volumetric demand using an approved, user-supplied LHV parameter.
- Source provenance, revisions, calculation snapshots and distinct BOM/BOQ contracts.
- Ruff, Pyright, Pytest and Alembic migration workflow.

The current desktop vertical slice supports project creation and local persistence, parameter management and the first gas appliance demand method. The lower heating value must be entered and approved in Parameter Registry before calculation. Gas pipe-network sizing and pressure-loss calculations, live product/poz catalogues, production BOM/BOQ and cost workflows, engineering editors and CAD/BIM operations remain under development.

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

- `src/mechpro/core`: application context, configuration and shared services.
- `src/mechpro/domain`: pure, typed engineering domain contracts.
- `src/mechpro/data`: persistence adapters and repositories.
- `src/mechpro/modules`: bounded application modules.
- `src/mechpro/ui`: PySide6 desktop control center.
- `docs/architecture`: architecture decisions and domain documentation.
- `docs/product`: product direction, scope and feature priorities.

The internal Python import namespace remains `mechpro` for source compatibility. The distributed desktop product, installer identity and user-facing application name are MechProX. AutoCAD and Revit remain external desktop applications accessed through bridge adapters. The previously working AutoCAD bridge is to be reused, not recreated as a proof of concept.
