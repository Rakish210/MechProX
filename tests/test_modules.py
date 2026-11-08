from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from mechprox.core.context import AppContext
from mechprox.core.module_registry import (
    ModuleDependencyCycleError,
    ModuleDependencyError,
    ModuleEntryPoint,
    ModuleHost,
    ModuleHostNotStartedError,
    ModuleManifest,
    ModulePageSpec,
    ModuleRegistrationError,
    ModuleRegistry,
    ModuleShutdownError,
    ModuleSpec,
    ModuleStartupError,
)


@dataclass
class FakeModule:
    name: str
    events: list[str] = field(default_factory=list)
    fail_on: str | None = None
    fail_stop: bool = False

    def configure(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.configure")
        if self.fail_on == "configure":
            raise RuntimeError("configure failed")

    def start(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.start")
        if self.fail_on == "start":
            raise RuntimeError("start failed")

    def stop(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.stop")
        if self.fail_stop:
            raise RuntimeError("stop failed")


def spec(
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


def test_registry_rejects_duplicate_module_ids() -> None:
    registry = ModuleRegistry()
    registry.register(spec("projects", lambda: FakeModule("projects")))

    with pytest.raises(ModuleRegistrationError, match="already registered"):
        registry.register(spec("projects", lambda: FakeModule("duplicate")))


def test_registry_rejects_incompatible_module_api() -> None:
    registry = ModuleRegistry()
    with pytest.raises(ModuleRegistrationError, match="requires API 2"):
        registry.register(
            spec("new-module", lambda: FakeModule("new-module"), api_version=2)
        )


def test_registry_requires_declared_dependencies() -> None:
    registry = ModuleRegistry()
    registry.register(
        spec("commercial", lambda: FakeModule("commercial"), dependencies=("catalogue",))
    )

    with pytest.raises(ModuleDependencyError, match="requires missing"):
        registry.startup_order()


def test_registry_rejects_dependency_cycles() -> None:
    registry = ModuleRegistry()
    registry.register(spec("alpha", lambda: FakeModule("alpha"), dependencies=("beta",)))
    registry.register(spec("beta", lambda: FakeModule("beta"), dependencies=("alpha",)))

    with pytest.raises(ModuleDependencyCycleError, match="dependency cycle"):
        registry.startup_order()


def test_startup_order_is_dependency_safe() -> None:
    registry = ModuleRegistry()
    registry.register(
        spec("commercial", lambda: FakeModule("commercial"), dependencies=("catalogue",))
    )
    registry.register(spec("catalogue", lambda: FakeModule("catalogue")))
    registry.register(spec("projects", lambda: FakeModule("projects")))

    assert [item.manifest.module_id for item in registry.startup_order()] == [
        "catalogue", "commercial", "projects"
    ]


def test_page_specs_are_namespaced_and_sorted_by_navigation_order() -> None:
    registry = ModuleRegistry()
    registry.register(
        spec(
            "engineering",
            lambda: FakeModule("engineering"),
            pages=(
                ModulePageSpec("calculations", "Hesaplamalar", lambda _ctx: object(), order=20),
                ModulePageSpec("model", "Mühendislik Verisi", lambda _ctx: object(), order=10),
            ),
        )
    )
    registry.register(
        spec(
            "workspace",
            lambda: FakeModule("workspace"),
            pages=(ModulePageSpec("projects", "Projeler", lambda _ctx: object(), order=0),),
        )
    )

    pages = registry.page_specs()
    assert [page.key for page in pages] == [
        "workspace.projects", "engineering.model", "engineering.calculations"
    ]


def test_registry_rejects_duplicate_page_ids_inside_a_module() -> None:
    registry = ModuleRegistry()
    duplicate_pages = (
        ModulePageSpec("home", "Home", lambda _ctx: object()),
        ModulePageSpec("home", "Another Home", lambda _ctx: object(), order=20),
    )

    with pytest.raises(ModuleRegistrationError, match="duplicate page IDs"):
        registry.register(spec("workspace", lambda: FakeModule("workspace"), pages=duplicate_pages))


def test_host_requires_start_before_pages_can_be_requested() -> None:
    registry = ModuleRegistry()
    registry.register(spec("workspace", lambda: FakeModule("workspace")))
    host = ModuleHost(registry, AppContext())

    with pytest.raises(ModuleHostNotStartedError):
        host.page_specs()


def test_host_configures_every_module_before_start_and_stops_in_reverse_order() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(spec("base", lambda: FakeModule("base", events)))
    registry.register(
        spec(
            "extension",
            lambda: FakeModule("extension", events),
            dependencies=("base",),
        )
    )
    context = AppContext()
    host = ModuleHost(registry, context)

    host.start()

    assert events == [
        "base.configure", "extension.configure", "base.start", "extension.start"
    ]
    assert context.services.is_frozen
    assert host.started_module_ids == ("base", "extension")

    host.stop()
    assert events[-2:] == ["extension.stop", "base.stop"]
    assert host.started_module_ids == ()


def test_host_rolls_back_even_the_module_whose_start_failed() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(spec("base", lambda: FakeModule("base", events)))
    registry.register(
        spec(
            "broken",
            lambda: FakeModule("broken", events, fail_on="start"),
            dependencies=("base",),
        )
    )
    host = ModuleHost(registry, AppContext())

    with pytest.raises(ModuleStartupError, match="startup failed"):
        host.start()

    assert events[-2:] == ["broken.stop", "base.stop"]
    assert host.started_module_ids == ()


def test_host_reports_shutdown_errors_after_stopping_all_modules() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(
        spec("base", lambda: FakeModule("base", events, fail_stop=True))
    )
    registry.register(
        spec("extension", lambda: FakeModule("extension", events), dependencies=("base",))
    )
    host = ModuleHost(registry, AppContext())
    host.start()

    with pytest.raises(ModuleShutdownError, match="base"):
        host.stop()

    assert events[-2:] == ["extension.stop", "base.stop"]


def test_discovery_loads_only_explicitly_enabled_entry_points() -> None:
    events: list[str] = []

    class FakeEntryPoint:
        name = "trusted-extension"

        def load(self) -> object:
            events.append("loaded")
            return lambda: spec("trusted-extension", lambda: FakeModule("trusted-extension"))

    registry = ModuleRegistry()
    fake_entry_point = FakeEntryPoint()
    discovered: tuple[ModuleEntryPoint, ...] = (fake_entry_point,)
    assert registry.discover_entry_points(discovered=discovered) == ()
    assert events == []

    assert registry.discover_entry_points(
        ("trusted-extension",), discovered=discovered
    ) == ("trusted-extension",)
    assert events == ["loaded"]
