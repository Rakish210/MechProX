from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from mechprox.core.context import AppContext
from mechprox.core.module_registry import (
    ModuleDependencyCycleError,
    ModuleDependencyError,
    ModuleHost,
    ModuleHostNotStartedError,
    ModuleManifest,
    ModulePageSpec,
    ModuleRegistry,
    ModuleRegistrationError,
    ModuleShutdownError,
    ModuleSpec,
    ModuleStartupError,
)
from mechprox.core.service_registry import (
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
    ServiceRegistry,
    ServiceRegistryFrozenError,
)


@dataclass
class RecordingModule:
    name: str
    events: list[str] = field(default_factory=list)
    fail_start: bool = False
    fail_stop: bool = False

    def configure(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.configure")

    def start(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.start")
        if self.fail_start:
            raise RuntimeError("deliberate startup failure")

    def stop(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.stop")
        if self.fail_stop:
            raise RuntimeError("deliberate shutdown failure")


def _spec(
    module_id: str,
    factory,
    *,
    dependencies: tuple[str, ...] = (),
    pages: tuple[ModulePageSpec, ...] = (),
    api_version: int = 1,
) -> ModuleSpec:
    return ModuleSpec(
        manifest=ModuleManifest(
            module_id=module_id,
            title=module_id.title(),
            version="1.0.0",
            api_version=api_version,
            dependencies=dependencies,
        ),
        factory=factory,
        pages=pages,
    )


def test_registry_sorts_modules_by_dependency_order() -> None:
    registry = ModuleRegistry()
    registry.register(_spec("commercial", RecordingModule, dependencies=("engineering",)))
    registry.register(_spec("engineering", RecordingModule, dependencies=("workspace",)))
    registry.register(_spec("workspace", RecordingModule))

    assert [item.manifest.module_id for item in registry.startup_order()] == [
        "workspace",
        "engineering",
        "commercial",
    ]


def test_registry_rejects_duplicate_and_incompatible_modules() -> None:
    registry = ModuleRegistry()
    registry.register(_spec("workspace", RecordingModule))

    with pytest.raises(ModuleRegistrationError, match="already registered"):
        registry.register(_spec("workspace", RecordingModule))

    with pytest.raises(ModuleRegistrationError, match="requires API 2"):
        registry.register(_spec("legacy", RecordingModule, api_version=2))


def test_registry_rejects_missing_dependencies() -> None:
    registry = ModuleRegistry()
    registry.register(_spec("engineering", RecordingModule, dependencies=("workspace",)))

    with pytest.raises(ModuleDependencyError, match="requires missing module 'workspace'"):
        registry.startup_order()


def test_registry_rejects_dependency_cycles() -> None:
    registry = ModuleRegistry()
    registry.register(_spec("first", RecordingModule, dependencies=("second",)))
    registry.register(_spec("second", RecordingModule, dependencies=("first",)))

    with pytest.raises(ModuleDependencyCycleError, match="cycle detected"):
        registry.startup_order()


def test_registry_builds_unique_navigation_pages_in_stable_order() -> None:
    registry = ModuleRegistry()
    registry.register(
        _spec(
            "workspace",
            RecordingModule,
            pages=(
                ModulePageSpec("projects", "Projects", lambda context: object(), order=20),
                ModulePageSpec("dashboard", "Dashboard", lambda context: object(), order=10),
            ),
        )
    )
    registry.register(
        _spec(
            "engineering",
            RecordingModule,
            dependencies=("workspace",),
            pages=(
                ModulePageSpec("model", "Model", lambda context: object(), order=30),
            ),
        )
    )

    assert [page.key for page in registry.page_specs()] == [
        "workspace.dashboard",
        "workspace.projects",
        "engineering.model",
    ]


def test_registry_rejects_duplicate_page_ids_inside_module() -> None:
    registry = ModuleRegistry()
    duplicate_pages = (
        ModulePageSpec("dashboard", "Dashboard", lambda context: object()),
        ModulePageSpec("dashboard", "Duplicate", lambda context: object()),
    )
    with pytest.raises(ModuleRegistrationError, match="duplicate page IDs"):
        registry.register(_spec("workspace", RecordingModule, pages=duplicate_pages))


def test_host_configures_all_then_starts_and_stops_in_reverse_order() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(
        _spec("workspace", lambda: RecordingModule("workspace", events))
    )
    registry.register(
        _spec(
            "engineering",
            lambda: RecordingModule("engineering", events),
            dependencies=("workspace",),
        )
    )
    context = AppContext()
    host = ModuleHost(registry, context)

    host.start()
    assert events == [
        "workspace.configure",
        "engineering.configure",
        "workspace.start",
        "engineering.start",
    ]
    assert host.started_module_ids == ("workspace", "engineering")
    assert context.services.is_frozen
    with pytest.raises(ModuleHostNotStartedError):
        ModuleHost(ModuleRegistry(), AppContext()).page_specs()  # empty host is valid

    host.stop()
    assert events[-2:] == ["engineering.stop", "workspace.stop"]
    host.stop()


def test_host_rolls_back_a_module_that_fails_partway_through_startup() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(_spec("workspace", lambda: RecordingModule("workspace", events)))
    registry.register(
        _spec(
            "failure",
            lambda: RecordingModule("failure", events, fail_start=True),
            dependencies=("workspace",),
        )
    )
    host = ModuleHost(registry, AppContext())

    with pytest.raises(ModuleStartupError, match="failure startup failed"):
        host.start()

    assert events[-2:] == ["failure.stop", "workspace.stop"]
    assert host.started_module_ids == ()


def test_host_reports_shutdown_errors_after_stopping_remaining_modules() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(_spec("workspace", lambda: RecordingModule("workspace", events)))
    registry.register(
        _spec(
            "engineering",
            lambda: RecordingModule("engineering", events, fail_stop=True),
            dependencies=("workspace",),
        )
    )
    host = ModuleHost(registry, AppContext())
    host.start()

    with pytest.raises(ModuleShutdownError, match="engineering"):
        host.stop()

    assert events[-2:] == ["engineering.stop", "workspace.stop"]


def test_service_registry_enforces_single_registration_and_freezing() -> None:
    class Repository:
        pass

    service = Repository()
    registry = ServiceRegistry()
    registry.register(Repository, service)

    assert registry.get(Repository) is service
    assert registry.require(Repository) is service
    with pytest.raises(ServiceAlreadyRegisteredError):
        registry.register(Repository, Repository())
    with pytest.raises(ServiceNotFoundError):
        registry.require(str)

    registry.freeze()
    with pytest.raises(ServiceRegistryFrozenError):
        registry.register(str, "late")
