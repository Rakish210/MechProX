# ADR-002: Common Engineering Data Model Contracts

## Status

Accepted for CEDM Version 1.

## Context

Multiple engineering disciplines, drawing/BIM adapters, calculation methods, BOM/BOQ and reporting must exchange the same traceable data without depending on the UI, persistence layer or external CAD/BIM applications.

## Decision

- Use immutable Pydantic domain contracts in a dedicated `mechprox.domain` package.
- Keep domain contracts independent from PySide6, SQLAlchemy, SQLite and vendor APIs.
- Use explicit typed variants for property values; reject unrecognized fields.
- Use Decimal magnitudes with explicit unit codes and Pint for offline dimensional validation/conversion.
- Represent engineering networks as graphs of object connectors and connections, not as a fixed linear pipe list.
- Separate physical ProductReference/BOM concepts from commercial PositionReference/BOQ concepts, joined by versioned mappings.
- Capture object revisions, parameter snapshots, calculation method/engine versions and source references in calculation runs.

## Alternatives considered

- Generic property dictionaries: rejected because they weaken validation, discoverability and static tooling.
- ORM classes as domain contracts: rejected because it couples engineering rules to persistence.
- A pipe-only network schema: rejected because air, fire, control and other engineering systems have different topologies.
- One combined BOM/BOQ line type: rejected because physical procurement items and commercial work positions are not equivalent.

## Consequences

The model is explicit and testable, and adapters can be developed independently. New engineering-specific types must be introduced through typed extensions and schema-versioned contracts. Unit definitions are shared and offline. Design coefficients and standard limits remain in a separate versioned Parameter Registry.
