# MechPro

**Modular mechanical engineering automation platform**

MechPro is a Python-first desktop engineering platform. The application coordinates deterministic engineering modules, traceable project data, product libraries, CAD/BIM adapters, quantity takeoff and technical reporting. AI models may orchestrate tools, but engineering results must come from versioned deterministic calculation methods.

## Technology baseline

- Python 3.11+
- PySide6 / Qt Widgets
- SQLAlchemy + SQLite + Alembic
- Pydantic domain contracts
- Pint for offline unit validation and conversion
- Pytest, Ruff and Pyright

## Install for development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run the desktop application:

```powershell
mechpro
```

Run validation:

```powershell
ruff check .
pyright
pytest -q
alembic upgrade head
```

The local application database is stored outside the repository under the user's `.mechpro` data directory by default. Set `MECHPRO_DATA_DIR` or `MECHPRO_DATABASE_URL` to override it.

## Architecture

- `src/mechpro/core`: shared application services and module registration.
- `src/mechpro/domain`: pure, typed Common Engineering Data Model contracts.
- `src/mechpro/data`: persistence adapters and SQLAlchemy metadata.
- `src/mechpro/modules`: application modules.
- `src/mechpro/ui`: PySide6 application shell.
- `docs/architecture`: architecture records, decisions and data-model documentation.

The domain layer is independent of the UI, database and CAD/BIM vendors. AutoCAD and Revit remain external desktop applications accessed through bridge adapters. The previously working AutoCAD bridge is to be reused; it must not be recreated as a new proof of concept.

## Common Engineering Data Model

The first CEDM contracts are in `src/mechpro/domain`. A synthetic, non-design natural-gas network can be built with:

```python
from mechpro.domain.example import create_natural_gas_reference_model
from mechpro.domain.validation import ModelValidator

model = create_natural_gas_reference_model()
report = ModelValidator().validate(model)
report.raise_for_errors()
```

The example is for data-model verification only. It does not contain a real gas calculation, public poz mapping or design values.
