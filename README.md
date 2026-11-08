# MechPro

**Uzman Mekanik Tesisat Mühendisliği Platformu**

MechPro is a Python-first desktop engineering platform. It coordinates a shared, traceable project model, deterministic engineering calculations, product and position libraries, CAD/BIM adapters, BOM/BOQ workflows and technical reporting. AI may orchestrate tools; engineering results must come from versioned deterministic methods.

## Current implementation

- PySide6 desktop control-center shell with project navigation.
- Local SQLite project workspace.
- Typed Pydantic Common Engineering Data Model (CEDM).
- Lossless JSON serialization and restore of project model snapshots.
- Unit-aware quantities using an offline Pint registry.
- Source provenance, revisions, calculation snapshots and distinct BOM/BOQ contracts.
- Ruff, Pyright, Pytest and Alembic migration workflow.

The current desktop vertical slice supports project creation and local persistence. Engineering editors, calculation engines, live catalogues, production BOM/BOQ generation and CAD/BIM operations are not yet implemented.

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
