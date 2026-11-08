# Deterministic Calculation Engine Framework — Version 1

## Purpose

The calculation framework executes versioned deterministic engineering methods. AI providers are not calculation engines. They may prepare requests or orchestrate tools, but numeric engineering outputs must be produced by registered, testable Python engines.

## Execution contracts

- `CalculationEngine` is the protocol implemented by a calculation method.
- `CalculationEngineRegistry` registers an engine by method code and method revision.
- `CalculationRequest` explicitly declares project, method revision, input object IDs, parameter codes, effective date, jurisdiction and standard references.
- `CalculationContext` exposes only the selected project metadata, input objects, resolved parameter revisions and selected standards. It does not expose the entire project model to an engine.
- `CalculationRunner` validates prerequisites, captures snapshots, executes the engine, validates output provenance and creates a `CalculationRun`.
- `run_and_save` appends completed or failed runs and results to the project snapshot.

## Input controls

Before an engine is called, the runner verifies:

1. The request project matches the supplied project model.
2. Every selected object exists in the project and has a controlled revision belonging to that object.
3. Object IDs, parameter codes and standard references are unique within the request.
4. Every engine-required parameter is explicitly requested.
5. Every parameter resolves to exactly one approved, effective revision under project > jurisdiction > global precedence.
6. Every standard and source reference required by the selected inputs is present in the project model.

The engine receives only declared inputs. It cannot silently inspect unrelated project objects through the execution context.

## Reproducibility

Each calculation input snapshot retains:

- Full typed engineering object snapshot and its controlled revision ID.
- Engineering property snapshots.
- Full parameter revision snapshots, including value, status, scope, dates and provenance.
- Source reference IDs.
- A SHA-256 snapshot hash.

The calculation run retains full standard reference snapshots, method code/revision, engine name/version, effective date and jurisdiction through its request hash, and a hash of the calculation inputs. Output hashes are computed from result values and provenance, excluding generated result IDs and timestamps so identical inputs and outputs produce identical hashes.

Engineering-purpose runs without full object and parameter revision snapshots are invalid. The synthetic reference model's demonstration run is explicitly marked as demonstration data and is not treated as an engineering result.

## Failure handling

Engine exceptions and invalid result provenance are converted into a persisted `FAILED` run with an error message. Failed runs are retained for audit and do not create result records. Preconditions that prevent a valid calculation request from being assembled raise a `CalculationPreconditionError` before a run is created.

## Output provenance

Every result may declare source object IDs, source parameter codes and standard reference IDs. The runner rejects results that reference objects, parameters or standards outside the captured calculation context.

## Current limitations

- The framework is implemented and tested with synthetic test engines only.
- No natural-gas, hydronic, ventilation, cooling or fire-protection production equation is included yet.
- Calculation result unit/dimensional contracts are carried by typed values, but method-specific output schemas and design-limit validation remain to be added.
- Source documents are referenced by IDs; source-document content hashing and archival snapshots will be integrated with the document/source management module.
- Cancellation, background execution, progress reporting and calculation comparison UI are future work.
