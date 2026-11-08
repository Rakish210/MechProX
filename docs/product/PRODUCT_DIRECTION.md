# MechProX — Product Direction

**Status:** Product direction baseline  
**Product:** MechProX — Uzman Mekanik Tesisat Mühendisliği Platformu

## 1. Product definition

MechProX is an engineering control center for mechanical building-services design. It is not intended to be only a CAD command pack, a block insertion tool, a calculator website or a takeoff estimator.

The system of record is one revision-controlled engineering project model. Design objects, spaces, systems, equipment, parameters, calculation runs, drawing references, product selections, material quantities, BOQ positions and cost records are linked to that model.

The intended end-to-end flow is:

`Project Model → Engineering Design → Deterministic Calculations → CAD/BIM Exchange → BOM → BOQ → Cost / Procurement → Technical Reports`

AI may interpret documents, suggest model updates, run workflows and identify inconsistencies. AI must not invent engineering dimensions, quantities, standards, unit prices or calculation results. Proposed data must retain source references, validation state and user approval where required.

## 2. Product workflow principles

The product combines five complementary workflow areas:

### A. Discipline-focused design and drafting

- Separate practical workflows for plumbing, heating, fire protection, ventilation, fan-coil and VRF systems.
- Reusable block, layer and drawing-style libraries.
- Faster placement and modification of engineering elements.
- Automatic or assisted riser/column diagrams and coordinated drawing outputs.
- Connect design operations to calculations, reports and quantity schedules.
- Provide discipline workspaces over the shared project model, not disconnected mini-applications.
- Store blocks, layer conventions, symbols and drawing templates as versioned library assets.
- Keep AutoCAD as the native drawing environment. MechProX controls engineering data and exchanges structured changes through the existing bridge.
- Derive schedules and quantities from model objects and verified drawing entities rather than from isolated CAD text labels.

### B. Engineering calculation catalogue

- A discoverable calculation catalogue organized by discipline, system and engineering purpose.
- Coverage spanning heating, cooling, ventilation, plumbing, fire protection, natural gas, compressed air and medical gas.
- Dedicated utilities such as unit conversion, scientific calculation, friction-factor calculation and fluid/air-property references.
- Method- and standard-labelled calculation workflows, including distinct gas pressure classes and fire-system calculation types.
- Build a searchable **Engineering Method Catalogue** with filters by discipline, system, purpose, applicable standard and input/output type.
- Each method has a stable code and revision, declared input contract, physical dimensions/units, validity and applicability conditions, equation/method notes, source and standard references, validation cases, output contract and limitations.
- Keep all coefficients, material properties, design limits and reference data in the versioned Parameter Registry. The algorithm implementation is versioned code; engineering values are data.
- Implement equations independently and validate them with hand calculations, trusted reference examples and regression tests. A website or example calculator is not treated as an authority for a governing standard or for every value shown in an example.

### C. Position-based quantity surveying and commercial control

- Position (poz) catalogues with descriptions, unit prices, analyses and transport or ancillary cost components.
- Custom positions and reusable analysis templates.
- Measurement sheets organized into work groups, sections, formulas and subtotals.
- Project cost estimates, price revisions, progress-payment and final-account workflows.
- Carry reusable quantities and position definitions between projects without overwriting a destination project's established data.
- Keep **BOM** and **BOQ** as distinct domains. BOM describes physical products/materials and their quantities. BOQ describes measured contractual work positions and their measurement rules. One BOQ position may consume several BOM items; a product can contribute to multiple positions.
- Add a configurable position catalogue with source agency, jurisdiction, publication/revision date, unit, technical description and licensing/provenance information.
- Support custom project/company positions, analysis recipes and reusable templates.
- Derive position quantities from spaces, systems and verified drawing/model objects. Measurement sheets need formulas, sections, deductions, subtotals and audit lineage.
- Cost build-ups may include material, labour, equipment, transport, waste and overhead components. Each rate and analysis is revision-controlled.
- Add estimate comparisons, supplier quotations, procurement exports and progress-payment controls as later commercial modules. Country-specific procurement legislation must be implemented as scoped rule packs, not hardcoded as a universal workflow.
- Provide backup, restore, revision comparison and protection against accidental overwrite.

### D. Drawing-to-quantity automation and AI-assisted review

- Process drawing sets and specifications from PDF and CAD formats.
- Extract proposed quantities and structured BOM entries.
- Highlight detected objects and check scope against specifications.
- Compare drawing revisions to identify added, removed or modified scope.
- Produce numbered RFIs with sheet references.
- Prepare estimate, vendor/RFQ and spreadsheet handoff data.
- Ingest PDF/DWG drawing sets, schedules and specifications; retain file fingerprints, sheet/page references and entity identifiers.
- Treat AI/vision extraction as **proposed observations**, not certified quantities. Show source overlays, confidence, detected unit/type, validation messages and an explicit accept/reject/edit workflow.
- Reconcile drawing observations with the engineering model to find missing, duplicated, conflicting or unconnected elements.
- Compare drawing revisions and generate traceable change sets.
- Generate draft RFIs that cite the exact drawing sheet, detail, specification clause or model object that caused the question.
- Export approved BOM, BOQ, estimate and procurement data to Excel/CSV and other defined exchange formats.

### E. Integrated engineering information management

- Maintain a single revision-controlled model connecting design, calculations, drawings, products, quantities and commercial records.
- Track the source, author, validity, approval state and revision of engineering data.
- Provide consistent project backup, recovery, audit history and revision comparison.
- Keep standards, calculation methods, parameter values and product/position catalogues independently versioned.
- Make every engineering result reproducible from its stored inputs and method revision.

## 3. Core product capabilities

### A. Engineering model and design workspace

- Project, building, level, space, discipline, system and network structure.
- Typed engineering objects: equipment, terminals, pipes, ducts, fittings, valves, pumps, devices, connectors and other discipline-specific elements.
- Graph connectivity with explicit ports and connection semantics.
- Properties with dimensional units, provenance, approval and revision.
- Source traceability to manual inputs, DWG entities, Revit UniqueIds, PDF pages/details and imported schedules.
- Discipline-specific editors and validation rules over the same model.

### B. Deterministic calculation and method catalogue

Every calculation method must define:

- Stable method code and method revision.
- Engineering purpose, scope and assumptions.
- Required inputs, dimensional contracts and input validation.
- Equation/algorithm description and calculation steps.
- Parameter and property revisions used.
- Applicable standard, edition, clauses and jurisdiction when relevant.
- Output types, units, warning/error conditions and limitations.
- Independent reference cases, regression tests and reproducibility metadata.

Calculation reports freeze the exact input object revisions, parameter snapshots, method revision, engine version, standard references and output. Updating a later parameter revision must never alter an earlier result.

### C. CAD/BIM integration

- AutoCAD and Revit remain separate native applications.
- Reuse the existing AutoCAD bridge; do not replace it with an in-app drawing canvas or repeat its proof of concept.
- Map model objects to drawing entities with source handles and drawing fingerprints.
- Support controlled round-trip changes, block/layer libraries, schedules and revision comparisons.
- Add Revit/IFC exchange and BIM coordination as a separate later integration.

### D. BOM, BOQ and commercial management

- BOM is product/material-oriented and procurement-ready.
- BOQ is position/measurement-rule-oriented and contract/estimate-ready.
- Mapping between products, assemblies, work positions and measurement rules is versioned, many-to-many and traceable.
- Material/labour/equipment analyses, unit-rate history, custom rates, supplier alternatives and quotation comparisons.
- Project estimates, work groups, measurement sheets, progress payment and final account as staged capabilities.

### E. AI orchestration and drawing intelligence

- AI uses typed tools to read files, query models, invoke deterministic calculations and prepare review proposals.
- AI output is labelled as extracted, inferred, proposed or approved; these states must not be conflated.
- Every proposed quantity or design edit links to the source and is reviewable.
- RFI drafts, scope checks, revision deltas, anomaly detection and report preparation are suitable AI-assisted workflows.
- Engineering calculations, quantity finalization and approval remain governed by deterministic services and user-controlled validation.

## 4. Prioritized delivery sequence

1. **Foundation integrity:** model, persistence, units, parameter/standard/source registry, revisions and backup/recovery.
2. **Natural-gas engineering vertical slice:** network editor, load aggregation, pipe sections, gas properties, method selection, pressure/velocity/diameter checks, reproducible report and validated reference cases.
3. **CAD drawing intelligence:** DWG/PDF ingestion, source mapping, block/layer library, drawing-model reconciliation and controlled AutoCAD bridge exchange.
4. **BOM/BOQ and cost:** product/poz catalogues, mapping rules, measurement sheets, rate analyses, estimates and procurement exports.
5. **Additional disciplines:** plumbing, heating, cooling, ventilation, fire, compressed air and medical gas, each delivered as a validated engineering vertical slice.
6. **BIM coordination:** Revit/IFC, 3D routing, clashes, model QA and coordinated schedules.
7. **AI orchestration:** document understanding, takeoff proposals, revision comparisons, RFI drafts and engineering review tools.

The ordering may be adjusted when dependencies justify it, but no discipline is considered production-ready merely because its UI or formula screen exists.

## 5. Engineering data and content policy

- Basic physical equations can be implemented independently, but third-party prose, diagrams, proprietary worksheets, code, tables and licensed databases are not to be copied.
- Standards are referenced by identifier, edition and clause. Full standard texts are only stored or distributed where licensing permits.
- Public unit-price and product catalogues require recorded source, publication date, usage rights and revision.
- No unverified web value, AI guess or example coefficient becomes a production parameter.
- Every source-derived value has provenance and an approval state.

## 6. Explicit non-goals

- Do not reproduce any third-party site's visual design or proprietary implementation.
- Do not replace AutoCAD with a basic in-app drawing imitation.
- Do not treat a PDF/DWG quantity detector as an engineering design engine.
- Do not mix BOM and BOQ into a single undifferentiated list.
- Do not let AI silently write or approve engineering model changes.
- Do not hardcode jurisdiction-specific values or procurement rules into calculation algorithms.
