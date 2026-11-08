from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Protocol

from PySide6.QtWidgets import QWidget

from mechprox.core.context import AppContext


PLATFORM_MODULE_API_VERSION = 1
MODULE_ENTRY_POINT_GROUP = "mechprox.modules"


class ModuleError(RuntimeError):
    """Base error for module registration and lifecycle failures."""


class ModuleRegistrationError(ModuleError, ValueError):
    """A module manifest or registration is invalid."""


class ModuleDependencyError(ModuleRegistrationError):
    """A declared module dependency cannot be satisfied."""


class ModuleDependencyCycleError(ModuleDependencyError):
    """The registered module dependency graph contains a cycle."""


class ModuleLifecycleError(ModuleError):
    """A module failed while configuring, starting, rendering or stopping."""


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    module_id: str
    title: str
    version: str
    api_version: int = PLATFORM_MODULE_API_VERSION
    dependencies: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    description: str = ""
    navigation_order: int = 100

    def __post_init__(self) -> None:
        module_id = self.module_id.strip()
        if not module_id or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789._-" for ch in module_id):
            raise ModuleRegistrationError(
                "Module IDs may contain lowercase letters, digits, dots, underscores and hyphens."
            )
        if not module_id[0].isalpha():
            raise ModuleRegistrationError("A module ID must start with a lowercase letter.")
        if not self.title.strip():
            raise ModuleRegistrationError("A module title is required.")
        if not self.version.strip():
            raise ModuleRegistrationError("A module version is required.")
        if self.api_version < 1:
            raise ModuleRegistrationError("Module API version must be positive.")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ModuleRegistrationError(f"Module '{module_id}' has duplicate dependencies.")
        if module_id in self.dependencies:
            raise ModuleRegistrationError(f"Module '{module_id}' cannot depend on itself.")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ModuleRegistrationError(f"Module '{module_id}' has duplicate capabilities.")
        if any(not item.strip() for item in (*self.dependencies, *self.capabilities)):
            raise ModuleRegistrationError(
                f"Module '{module_id}' has an empty dependency or capability."
            )


class PlatformModule(Protocol):
    """Public lifecycle contract implemented by every first-party or installed module."""

    def configure(self, context: AppContext) -> None:
        """Register services and integrations before the host freezes the service registry."""

    def start(self, context: AppContext) -> None:
        """Start resources after every module has been configured."""

    def create_widget(self, context: AppContext) -> QWidget:
        """Create the module's desktop workspace."""

    def on_activated(self, context: AppContext, widget: QWidget) -> None:
        """Refresh or prepare the workspace when the user opens it."""

    def stop(self, context: AppContext) -> None:
        """Release resources in reverse dependency order."""


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    manifest: ModuleManifest
    factory: Callable[[], PlatformModule]


class ModuleRegistry:
    """Module catalogue with API compatibility and dependency validation."""

    def __init__(self, *, api_version: int = PLATFORM_MODULE_API_VERSION) -> None:
        if api_version < 1:
            raise ValueError("Platform module API version must be positive.")
        self._api_version = api_version
        self._modules: dict[str, ModuleSpec] = {}

    def register(self, spec: ModuleSpec) -> None:
        manifest = spec.manifest
        if manifest.api_version != self._api_version:
            raise ModuleRegistrationError(
                f"Module '{manifest.module_id}' requires API {manifest.api_version}; "
                f"host provides API {self._api_version}."
            )
        if manifest.module_id in self._modules:
            raise ModuleRegistrationError(
                f"Module '{manifest.module_id}' is already registered."
            )
        self._modules[manifest.module_id] = spec

    def load_entry_points(self, enabled_module_ids: Iterable[str]) -> tuple[str, ...]:
        """Load explicitly enabled, trusted Python packages registered as MechProX modules.

        Third-party modules execute Python code in the application process. Only
        install and enable packages from trusted sources.
        """
        enabled = set(enabled_module_ids)
        loaded: list[str] = []
        available = {point.name: point for point in entry_points(group=MODULE_ENTRY_POINT_GROUP)}
        unknown = enabled - set(available)
        if unknown:
            raise ModuleRegistrationError(
                "Enabled module entry points are not installed: " + ", ".join(sorted(unknown))
            )
        for module_id in sorted(enabled):
            point = available[module_id]
            try:
                factory = point.load()
                spec = factory()
            except Exception as exc:  # noqa: BLE001 - isolate plugin import boundary
                raise ModuleRegistrationError(
                    f"Could not load installed module '{module_id}': {exc}"
                ) from exc
            if not isinstance(spec, ModuleSpec):
                raise ModuleRegistrationError(
                    f"Entry point '{module_id}' must return a ModuleSpec."
                )
            if spec.manifest.module_id != module_id:
                raise ModuleRegistrationError(
                    f"Entry point '{module_id}' returned module "
                    f"'{spec.manifest.module_id}'."
                )
            self.register(spec)
            loaded.append(module_id)
        return tuple(loaded)

    def get(self, module_id: str) -> ModuleSpec:
        try:
            return self._modules[module_id]
        except KeyError as exc:
            raise ModuleRegistrationError(f"Module '{module_id}' is not registered.") from exc

    def all(self) -> tuple[ModuleSpec, ...]:
        return tuple(
            sorted(
                self._modules.values(),
                key=lambda spec: (spec.manifest.navigation_order, spec.manifest.module_id),
            )
        )

    def startup_order(self) -> tuple[ModuleSpec, ...]:
        for spec in self._modules.values():
            for dependency in spec.manifest.dependencies:
                if dependency not in self._modules:
                    raise ModuleDependencyError(
                        f"Module '{spec.manifest.module_id}' requires missing module "
                        f"'{dependency}'."
                    )

        ordered: list[ModuleSpec] = []
        visiting: list[str] = []
        visited: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in visited:
                return
            if module_id in visiting:
                cycle = " -> ".join((*visiting, module_id))
                raise ModuleDependencyCycleError(f"Module dependency cycle: {cycle}.")
            visiting.append(module_id)
            spec = self._modules[module_id]
            for dependency in spec.manifest.dependencies:
                visit(dependency)
            visiting.pop()
            visited.add(module_id)
            ordered.append(spec)

        for module_id in sorted(self._modules):
            visit(module_id)
        return tuple(ordered)

    def providers(self, capability: str) -> tuple[ModuleSpec, ...]:
        return tuple(spec for spec in self.all() if capability in spec.manifest.capabilities)


class ModuleHost:
    """Runs module lifecycles and creates their desktop workspaces on demand."""

    def __init__(self, registry: ModuleRegistry, context: AppContext) -> None:
        self.registry = registry
        self.context = context
        self._instances: dict[str, PlatformModule] = {}
        self._started: list[str] = []
        self._widgets: dict[str, QWidget] = {}
        self._attempted = False
        self._stopped = False

    def start(self) -> None:
        if self._attempted:
            raise ModuleLifecycleError("A module host can only be started once.")
        self._attempted = True
        ordered = self.registry.startup_order()
        try:
            for spec in ordered:
                try:
                    instance = spec.factory()
                except Exception as exc:  # noqa: BLE001 - module factory boundary
                    raise ModuleLifecycleError(
                        f"Module '{spec.manifest.module_id}' could not be constructed: {exc}"
                    ) from exc
                self._validate_instance(spec.manifest.module_id, instance)
                self._instances[spec.manifest.module_id] = instance

            for spec in ordered:
                module_id = spec.manifest.module_id
                try:
                    self._instances[module_id].configure(self.context)
                except Exception as exc:  # noqa: BLE001 - module boundary
                    raise ModuleLifecycleError(
                        f"Module '{module_id}' failed during configuration: {exc}"
                    ) from exc

            self.context.services.freeze()

            for spec in ordered:
                module_id = spec.manifest.module_id
                try:
                    self._instances[module_id].start(self.context)
                except Exception as exc:  # noqa: BLE001 - module boundary
                    raise ModuleLifecycleError(
                        f"Module '{module_id}' failed during startup: {exc}"
                    ) from exc
                self._started.append(module_id)
        except Exception:
            self._stop_started(suppress_errors=True)
            raise

    def manifests(self) -> tuple[ModuleManifest, ...]:
        return tuple(spec.manifest for spec in self.registry.all())

    def widget(self, module_id: str) -> QWidget:
        if module_id not in self._started:
            raise ModuleLifecycleError(
                f"Module '{module_id}' is not started; call ModuleHost.start() first."
            )
        if module_id not in self._widgets:
            try:
                widget = self._instances[module_id].create_widget(self.context)
            except Exception as exc:  # noqa: BLE001 - UI creation boundary
                raise ModuleLifecycleError(
                    f"Module '{module_id}' failed to create its workspace: {exc}"
                ) from exc
            if not isinstance(widget, QWidget):
                raise ModuleLifecycleError(
                    f"Module '{module_id}' did not return a QWidget workspace."
                )
            self._widgets[module_id] = widget
        return self._widgets[module_id]

    def activate(self, module_id: str) -> None:
        widget = self.widget(module_id)
        try:
            self._instances[module_id].on_activated(self.context, widget)
        except Exception as exc:  # noqa: BLE001 - module activation boundary
            raise ModuleLifecycleError(
                f"Module '{module_id}' failed while activating its workspace: {exc}"
            ) from exc

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        failures = self._stop_started(suppress_errors=False)
        if failures:
            raise ModuleLifecycleError("; ".join(failures))

    def _stop_started(self, *, suppress_errors: bool) -> list[str]:
        failures: list[str] = []
        for module_id in reversed(self._started):
            try:
                self._instances[module_id].stop(self.context)
            except Exception as exc:  # noqa: BLE001 - continue releasing remaining modules
                failures.append(f"{module_id}: {exc}")
                self.context.logger.exception("Module '%s' failed during shutdown", module_id)
        self._started.clear()
        if failures and not suppress_errors:
            return failures
        return failures

    @staticmethod
    def _validate_instance(module_id: str, instance: object) -> None:
        required = ("configure", "start", "create_widget", "on_activated", "stop")
        missing = [
            member for member in required
            if not callable(getattr(instance, member, None))
        ]
        if missing:
            raise ModuleLifecycleError(
                f"Module '{module_id}' does not implement required lifecycle methods: "
                + ", ".join(missing)
            )
