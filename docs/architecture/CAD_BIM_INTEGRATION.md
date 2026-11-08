# CAD/BIM Integration

## Policy
- No embedded CAD/BIM editor.
- AutoCAD and Revit run as independent applications.
- Python platform communicates via isolated bridge components (IPC/sockets/named pipes).
- Engineering logic stays in core modules; bridges only transport data/commands.

## AutoCAD
- Evaluate AutoCAD .NET/COM API + external bridge; DWG/DXF exchange.

## Revit
- Revit API requires in-process add-in; bridge via IPC to external process.
