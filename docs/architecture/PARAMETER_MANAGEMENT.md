# Parameter Registry — Version 1

## Purpose

The Parameter Registry is the authoritative, versioned source for engineering inputs, design criteria, limits, coefficients and other configurable values. Calculation algorithms remain Python code; engineering values and their source data do not.

## Implemented contracts

- `ParameterDefinition`: stable parameter identity, discipline/category, value kind and dimensional contract.
- `ParameterRevision`: immutable value revision, approval state, provenance, standards, validity dates and scope.
- `ParameterRegistry`: portable snapshot of definitions and revisions.
- `ParameterRegistryRepository`: SQLite persistence, typed restore, dimensional validation and resolution.
- `resolve_parameter`: deterministic scope resolution.

## Scope precedence

A resolver uses only approved revisions whose validity interval includes the explicitly supplied effective date. Precedence is:

1. Project-specific revision.
2. Jurisdiction-specific revision.
3. Global revision.

Two applicable revisions at the same highest priority are an ambiguity error. The resolver does not silently choose the newest row. Draft, superseded and withdrawn values are never used for engineering resolution.

## Units and values

Quantity definitions must declare both an expected physical dimension and a canonical unit. Every quantity revision carries its own unit. Pint validates dimensional compatibility and conversion compatibility. Scalar parameters do not declare physical units. Currency must use a separately modeled monetary value type; it must not be treated as a physical quantity.

## Governance

Approved revisions require an approver identity. Each revision retains its creator, approval identity, source references, standard references, effective dates and change summary. New values create new revisions; existing revisions are not edited in place.

## Explicit limitations

- The repository stores typed parameter records and supports deterministic resolution.
- Source and standard reference identifiers are preserved, but a source-document ingestion/catalogue workflow is not yet implemented.
- No authoritative national standard values or public-works coefficients are seeded. The registry starts empty by design.
- Project-specific override approval workflows and a dedicated registry UI are future work.
