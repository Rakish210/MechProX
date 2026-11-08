# MechPro

**Uzman Mekanik Tesisat Mühendisliği Platformu**

MechPro is a Python-first desktop engineering platform. It coordinates a shared, traceable project model, deterministic engineering calculations, product and position libraries, CAD/BIM adapters, BOM/BOQ workflows and technical reporting. AI may orchestrate tools; engineering results must come from versioned deterministic methods.

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

The current desktop vertical slice supports project creation and local persistence. Parameter Registry persistence, deterministic value resolution and basic registry management are implemented. The first gas appliance demand method is available in the desktop calculation page. The LHV must be entered and approved in Parameter Registry before calculation. Gas pipe sizing and pressure-loss calculations, engineering editors, live product/poz catalogues, production BOM/BOQ generation and CAD/BIM operations are not yet implemented.

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
mechpro
```

Validation:

```powershell
ruff check .
pyright
pytest -q
alembic upgrade head
```

By default, local data is stored outside the repository in `%USERPROFILE%\.mechpro`. Set `MECHPRO_DATA_DIR` or `MECHPRO_DATABASE_URL` to override the location.

## Architecture

- `src/mechpro/core`: application context, configuration and shared services.
- `src/mechpro/domain`: pure, typed engineering domain contracts.
- `src/mechpro/data`: persistence adapters and repositories.
- `src/mechpro/modules`: bounded application modules.
- `src/mechpro/ui`: PySide6 desktop control center.
- `docs/architecture`: architecture decisions and domain documentation.

The domain layer remains independent of UI, persistence and CAD/BIM vendors. AutoCAD and Revit remain external desktop applications accessed through bridge adapters. The previously working AutoCAD bridge is to be reused, not recreated as a proof of concept.
