# System Architecture

## Style
Modular Monolith (Python). Single deployable application with internal modules and plugin contracts. No microservices.

## Layers
1. Presentation (PySide6 Qt Widgets desktop UI)
2. Application/Orchestration (use cases, AI tool orchestration)
3. Domain (engineering rules, calculations via deterministic engines)
4. Infrastructure (SQLite/SQLAlchemy/Alembic, file storage, CAD/BIM bridges, providers)

## Core principles
- AI models orchestrate tools; engineering logic is deterministic and independently testable.
- No hardcoded engineering parameters; externalized versioned data sources.
- Modules communicate via typed contracts; no circular dependencies.
- CAD/BIM remain external; bridges isolate integration.

## Shared core
- Common Engineering Data Model
- Central Engineering Parameter Registry
- Calculation engine framework
- Plugin/module registry
- Validation & revision services
