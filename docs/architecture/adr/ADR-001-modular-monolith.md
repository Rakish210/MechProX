# ADR-001: Modular Monolith over Microservices

## Status
Proposed

## Context
Small team, AI-assisted development, need deterministic engineering core.

## Decision
Use a modular monolith with typed module contracts and plugin registry.

## Alternatives
Microservices (rejected: unnecessary infra/ops overhead).

## Consequences
Simpler deployment and testing; requires discipline to avoid coupling.
