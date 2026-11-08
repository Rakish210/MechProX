# MechProX Module System

## Purpose

MechProX is a platform host. Mechanical disciplines, commercial workflows, drawing adapters, reporting and future automation features are modules hosted by the same application. A module must not create its own database, application shell or competing project model.

## Module package contract

The current desktop host uses these public types from `mechprox.core.module_registry`:

- `ModuleManifest`: stable module ID, display title, package version, host API version, dependencies and capabilities.
- `ModulePageSpec`: one or more navigation workspaces supplied by the module.
- `ModuleSpec`: manifest, zero-argument module factory and page contributions.
- `PlatformModule`: configure, start and stop lifecycle methods.
- `ModuleRegistry`: validates module IDs, page IDs, API compatibility and dependency graph.
- `ModuleHost`: creates module instances, configures all modules, freezes application services, starts modules in dependency order and stops them in reverse order.

Module IDs are stable machine identifiers. Page IDs are unique within their module. The fully-qualified page key is `<module-id>.<page-id>`.

A module's `configure()` phase may register services and integrations. All modules are configured before any module starts. After configuration, the shared service registry is frozen so that runtime behavior cannot be changed by accidental late service registration.

The composition root creates repositories and platform services. Modules obtain them from `AppContext.services`; they do not open databases or construct global application dependencies themselves.

## Built-in modules

First-party module manifests and their initial pages are declared in `mechprox.modules.builtin`. The application shell reads page contributions from `ModuleHost.page_specs()`; it does not contain a hard-coded list of engineering modules or page constructors.

Current built-in module groups:

| Module | Responsibility |
|---|---|
| `workspace` | Project dashboard and project lifecycle |
| `engineering` | Common engineering model and calculation workspace |
| `reference-data` | Parameters, sources, standards, products and positions |
| `commercial` | BOM / BOQ and quantity workflows |
| `integrations` | CAD / BIM adapter hosting boundary |
| `reporting` | Technical and commercial report boundary |
| `administration` | Local application and recovery settings |

These are platform-level boundaries, not a commitment that each future engineering discipline must have its own process or database. A discipline module can contribute multiple workspaces and use the shared engineering model and services.

## Third-party module installation

A separately packaged module can declare a Python entry point in its own `pyproject.toml`:

```toml
[project.entry-points."mechprox.modules"]
example-hydronics = "example_hydronics.module:create_module"
```

The `create_module()` function must return a `ModuleSpec` compatible with the installed MechProX module API. It must declare all module dependencies and the page factories it contributes.

An entry-point package is not loaded merely because it is installed. Its entry-point name must be included in the local MechProX configuration under `enabled_module_packages`. This prevents an unrelated installed package from being executed implicitly.

Python entry-point modules run in the MechProX process and are **not sandboxed**. Only install and enable trusted packages. A future out-of-process extension protocol would be required for untrusted third-party code.

## Dependency and lifecycle rules

1. Module dependencies must exist before the module host starts.
2. The registry rejects dependency cycles and incompatible host API versions.
3. Dependencies configure and start before dependants.
4. Every module is configured before the first module starts.
5. The service registry is frozen after the configuration phase.
6. Shutdown is reverse dependency order. A failure in one module must not prevent other modules from being stopped.
7. If a module fails during its own startup, its stop handler is also invoked to release partially acquired resources.
8. UI page factories receive the shared `AppContext`. They do not own global service construction.

## Current scope and explicit limitations

This is the first module-host foundation. It provides in-process module registration, dependency/lifecycle management and dynamic desktop page composition. It does **not** yet provide:

- A GUI module marketplace or automatic package installer.
- Sandboxed or out-of-process add-ons.
- Database schema migration isolation per module.
- Cross-module permission enforcement or capability-based authorization.
- A stable public binary/plugin ABI for independent commercial distribution.
- Hot installation, hot unload or live module replacement while a project is open.

Those capabilities require separate design and security work. The current API is versioned so future host changes can be validated rather than silently breaking installed modules.

## Verification

The module test suite must cover duplicate IDs, host API incompatibility, missing dependencies, dependency cycles, dependency-safe startup, page registration, explicit entry-point enabling, startup rollback and reverse-order shutdown. The UI startup test must build the actual desktop shell from the built-in module registry.
