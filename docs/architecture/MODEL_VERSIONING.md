# Model Versioning and Reproducibility

## Schema version

Every EngineeringModel snapshot carries a `schema_version`. The current first contract is `1.0`. A future incompatible contract change must add a migration path and update compatibility tests; it must not silently reinterpret persisted project data.

## Object revisions

Revision records identify the state of a project or engineering object. A revision contains an object ID, revision code, state, optional content hash, parent revision and change metadata. A controlled object points to the revision that represents its current state.

Approved and superseded revisions are historical records. An edit creates a new revision; it does not mutate a previous revision in place.

## Calculation snapshots

A CalculationRun captures:
- Calculation method code and method revision.
- Calculation engine name and engine version.
- Calculation purpose and execution state.
- Input engineering object IDs and exact object revision IDs.
- Typed property snapshots and parameter values/revisions.
- Source references and applicable standard-reference IDs.
- Input and output hashes.

A subsequent change to a pipe, equipment, parameter or standard must not alter the snapshot held by an earlier run.

## Catalogue versioning

Product, position and position-product mapping records carry catalogue or mapping revision information. A mapping includes its measurement-rule code and version. A later mapping update must create a new version rather than changing the interpretation of an issued BOQ retroactively.

## Migration policy

- Schema changes are additive where possible.
- Breaking changes require an explicit schema-version increment and migration.
- Historical calculation records remain readable after migration.
- Never delete source IDs or revision links during migration.
- Migration tests must cover serialization round-trip and preservation of calculation input snapshots.
