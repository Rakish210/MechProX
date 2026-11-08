# Technology Evaluation

## Desktop UI
- PySide6 + Qt Widgets: mature, cross-platform, good for desktop engineering tools. Alternative: PyQt6 (licensing). Recommendation: PySide6 (LGPL).

## Persistence
- SQLite + SQLAlchemy + Alembic: simple, local-first, migration support. Good for small team.

## Geometry
- 2D: evaluate `shapely`, `ezdxf` (DXF I/O), `geomdl`. 
- 3D/BIM: evaluate `ifcopenshell`, `trimesh`, `pyglet`/`vtk`. Need PoC.

## AI
- Provider abstraction (local/cloud) via OpenAI-compatible API; tool/function calling. Evaluate Ollama, llama.cpp, vLLM, OpenRouter.

## CAD/BIM bridges
- AutoCAD: external process via COM/ActiveX or .NET plugin + socket/IPC; not embedded.
- Revit: external Revit add-in + IPC (Revit API requires in-process add-in; bridge via named pipes/sockets).

## Testing
- pytest, hypothesis for property-based tests, golden-file regression for calculations.
