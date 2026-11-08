from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from PySide6.QtWidgets import QWidget

from mechprox.core.context import AppContext
from mechprox.core.module_registry import (
    ModuleDependencyCycleError,
    ModuleDependencyError,
    ModuleHost,
    ModuleLifecycleError,
    ModuleManifest,
    ModuleRegistry,
    ModuleRegistrationError,
    ModuleSpec,
)


@dataclass
class FakeModule:
    name: str
    events: list[str] = field(default_factory=list)
    fail_on: str | None = None

    def configure(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.configure")
        if self.fail_on == "configure":
            raise RuntimeError("configure failed")

    def start(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.start")
        if self.fail_on == "start":
            raise RuntimeError("start failed")

    def create_widget(self, context: AppContext) -> QWidget:
        self.events.append(f"{self.name}.widget")
        if self.fail_on == "widget":
            raise RuntimeError("widget failed")
        return QWidget()

    def on_activated(self, context: AppContext, widget: QWidget) -> None:
        self.events.append(f"{self.name}.activate")

    def stop(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.stop")


def spec(
    module_id: str,
    factory,
    *,
    dependencies: tuple[str, ...] = (),
    order: int = 100,
) -> ModuleSpec:
    return ModuleSpec(
        manifest=ModuleManifest(
            module_id=module_id,
            title=module_id.title(),
            version="1.0.0",
            dependencies=dependencies,
            navigation_order=order,
        ),
        factory=factory,
    )


def test_registry_rejects_duplicate_module_ids() -> None:
    registry = ModuleRegistry()
    registry.register(spec("projects", lambda: FakeModule("projects")))

    with pytest.raises(ModuleRegistrationError, match="already registered"):
        registry.register(spec("projects", lambda: FakeModule("duplicate")))


def test_registry_rejects_incompatible_module_api() -> None:
    registry = ModuleRegistry()
    incompatible = ModuleSpec(
        manifest=ModuleManifest(
            module_id="incompatible",
            title="Incompatible",
            version="1.0",
            api_version=2,
        ),
        factory=lambda: FakeModule("incompatible"),
    )

    with pytest.raises(ModuleRegistrationError, match="requires API 2"):
        registry.register(incompatible)


def test_registry_requires_declared_dependencies() -> None:
    registry = ModuleRegistry()
    registry.register(
        spec("commercial", lambda: FakeModule("commercial"), dependencies=("catalogue",))
    )

    with pytest.raises(ModuleDependencyError, match="requires missing module 'catalogue'"):
        registry.startup_order()


def test_registry_rejects_dependency_cycles() -> None:
    registry = ModuleRegistry()
    registry.register(spec("alpha", lambda: FakeModule("alpha"), dependencies=("beta",)))
    registry.register(spec("beta", lambda: FakeModule("beta"), dependencies=("alpha",)))

    with pytest.raises(ModuleDependencyCycleError, match="dependency cycle"):
        registry.startup_order()


def test_startup_order_is_dependency_safe_and_navigation_order_is_separate() -> None:
    registry = ModuleRegistry()
    registry.register(spec("commercial", lambda: FakeModule("commercial"), dependencies=("catalogue",), order=1))
    registry.register(spec("catalogue", lambda: FakeModule("catalogue"), order=20))
    registry.register(spec("projects", lambda: FakeModule("projects"), order=10))

    assert [item.manifest.module_id for item in registry.startup_order()] == [
        "catalogue", "commercial", "projects"
    ]
    assert [item.manifest.module_id for item in registry.all()] == [
        "commercial", "projects", "catalogue"
    ]


def test_host_configures_all_modules_before_start_and_freezes_services() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(spec("base", lambda: _EventModule("base", events)))
    registry.register(
        spec("extension", lambda: _EventModule("extension", events), dependencies=("base",))
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


def test_host_reuses_workspace_and_runs_activation_hook(qt_app) -> None:
    module = FakeModule("projects")
    registry = ModuleRegistry()
    registry.register(spec("projects", lambda: module))
    host = ModuleHost(registry, AppContext())
    host.start()

    first = host.widget("projects")
    second = host.widget("projects")
    host.activate("projects")

    assert first is second
    assert module.events.count("projects.widget") == 1
    assert module.events[-1] == "projects.activate"
    host.stop()


def test_host_rolls_back_started_modules_when_later_module_fails() -> None:
    events: list[str] = []
    registry = ModuleRegistry()
    registry.register(spec("base", lambda: _EventModule("base", events)))
    registry.register(
        spec(
            "broken",
            lambda: _EventModule("broken", events, fail_on="start"),
            dependencies=("base",),
        )
    )
    host = ModuleHost(registry, AppContext())

    with pytest.raises(ModuleLifecycleError, match="failed during startup"):
        host.start()

    assert events[-1] == "base.stop"
    assert host.started_module_ids == ()


class _EventModule(FakeModule):
    def __init__(self, name: str, events: list[str], fail_on: str | None = None) -> None:
        super().__init__(name, events, fail_on)

    def configure(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.configure")

    def start(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.start")
        if self.fail_on == "start":
            raise RuntimeError("start failed")

    def stop(self, context: AppContext) -> None:
        self.events.append(f"{self.name}.stop")


@pytest.fixture
def qt_app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app
