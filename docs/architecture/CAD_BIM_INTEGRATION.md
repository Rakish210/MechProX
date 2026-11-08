# CAD/BIM Integration

## User-facing architecture

- The Python platform does not embed a CAD or BIM drawing editor.
- AutoCAD and Revit run as independent desktop applications.
- The platform communicates with them through isolated bridge adapters.
- Engineering calculations, domain rules, product selection and quantity logic remain in Python modules.
- Bridges transport commands and structured data and invoke the host application's supported API.

## AutoCAD

### Status

The product owner confirms that an AutoCAD bridge has worked in earlier development. Repeating an AutoCAD proof of concept or rewriting the bridge is explicitly out of scope.

Previously recorded compatibility context:
- AutoCAD 2021.
- .NET Framework 4.8.
- Existing bridge artifact was previously built as `MekanikCadBridge.dll` under a `bin/Release/net48` output path.

The existing source project or compiled artifact is not present in the inspected `phase-1/core-foundation` repository tree. The integration task must locate and reuse the existing implementation. Its actual communication protocol must be read from that implementation; do not assume or replace it without evidence.

The bridge should remain a thin AutoCAD adapter. No mechanical engineering calculations or commercial business rules belong inside it.

### Integration requirements

- Open or attach to the intended AutoCAD session.
- Read drawing entities and preserve native handles/identifiers.
- Read and write engineering metadata on supported entities.
- Create or update drawing entities through the existing bridge capabilities.
- Return structured responses and explicit errors to the Python host.
- Keep DWG files and AutoCAD's drawing UI under AutoCAD's control.

## Revit

Revit integration is a separate, not-yet-implemented adapter.

The integration design must account for Revit's in-process .NET API, transaction requirements and supported external-command/event mechanisms. Prefer native Revit MEP elements (Pipe, Duct, fittings, equipment and families) over generic solids when producing an editable MEP model.

The Revit bridge implementation and 3D generation technology remain open until their specific integration approach is selected and validated.

## Inter-process contract

The Python application should communicate with adapters through versioned, typed request/response contracts. The transport mechanism can differ by adapter and must be based on the actual host integration. The contract must include correlation IDs, schema versions, structured errors and timeout/cancellation behavior.
