# Engineering Data Model

## Common model (conceptual)
- Project, Discipline, System, Equipment, Component, Connection, Drawing, Revision.
- Quantities with units; materials; standards references.
- BOM/BOQ items derived from components and positions.

## Storage
- SQLite relational core; SQLAlchemy ORM; Alembic migrations.
- Files (DXF, IFC, PDF) referenced by path/hash, not embedded.

## Versioning
- Revision entities for drawings/specs; parameter sets versioned.
