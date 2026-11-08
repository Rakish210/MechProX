# Open Decisions

## Still open

- 2D geometry and drawing-analysis library selection (including DXF parsing, geometric operations and DWG access strategy).
- 3D geometry kernel and IFC/BIM exchange architecture.
- Revit add-in hosting, external communication and native MEP element creation strategy.
- Local AI model baseline, tool-calling reliability, hardware profiles and evaluation criteria.
- Canonical parameter/standard source strategy: authoritative database records versus versioned import/seed packages.
- Product catalogue and public-works position (poz) ingestion, licensing and update workflow.
- Desktop packaging and application update strategy.
- Backup, recovery and project portability policy.

## Resolved or deliberately not reopened

- **AutoCAD bridge proof of concept:** The product owner confirms that a previous bridge worked (AutoCAD 2021 / .NET Framework 4.8 context). Do not repeat the PoC or rewrite it. Reuse the existing source/artifact and inspect its actual protocol when integration begins. The bridge source/artifact is not currently present in the inspected `phase-1/core-foundation` repository tree, so locating it is an integration prerequisite rather than a technology PoC.

## Decision discipline

Open decisions must be resolved with evidence appropriate to their risk. Do not delay unrelated foundation or data-model work while a later adapter decision remains open. Record accepted decisions and their consequences in ADRs.
