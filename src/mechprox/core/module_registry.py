from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Protocol

from mechprox.core.context import AppContext


MODULE_ENTRY_POINT_GROUP = "mechprox.modules"
PLATFORM_MODULE_API_VERSION = 1
_MODULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*$")
_PAGE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")


class ModuleError(RuntimeError):
    """Base exception for module discovery, validation and lifecycle failures."""


class ModuleRegistrationError(ModuleError, ValueError):
    """Raised when a module manifest is invalid or conflicts with the host."""


class ModuleDependencyError(ModuleRegistrationError):
    """Raised when a module dependency cannot be satisfied."""


class ModuleDependencyCycleError(ModuleDependencyError):
    """Raised when the module dependency graph contains a cycle."""


class ModuleStartupError(ModuleError):
    """Raised when a module fails to configure or start."""


class ModuleShutdownError(ModuleError):
    """Raised after shutdown when one or more modules fail to stop."""


class ModuleHostNotStartedError(ModuleError):
    """Raised when module pages are requested before the host starts."""


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    module_id: str
    title: str
    version: str
    api_version: int = PLATFORM_MODULE_API_VERSION
    dependencies: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _MODULE_ID_PATTERN.fullmatch(self.module_id.strip()):
            raise ModuleRegistrationError(
                "Module IDs must start with a lowercase letter and contain only "
                "lowercase letters, digits, dots, underscores or hyphens."
            )
        if not self.title.strip() or not self.version.strip():
            raise ModuleRegistrationError("Module title and version are required.")
        if self.api_version < 1:
            raise ModuleRegistrationError("Module API version must be positive.")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ModuleRegistrationError(
                f"Module '{self.module_id}' declares duplicate dependencies."
            )
        if self.module_id in self.dependencies:
            raise ModuleRegistrationError(
                f"Module '{self.module_id}' cannot depend on itself."
            )
        if any(not _MODULE_ID_PATTERN.fullmatch(item) for item in self.dependencies):
            raise ModuleRegistrationError(
                f"Module '{self.module_id}' declares an invalid dependency ID."
            )
        if any(not _MODULE_ID_PATTERN.fullmatch(item) for item in self.capabilities):
            raise ModuleRegistrationError(
                f"Module '{self.module_id}' has an empty dependency or capability."
            )
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ModuleRegistrationError(
                f"Module '{self.module_id}' declares duplicate capabilities."
            )


@dataclass(frozen=True, slots=True)
class ModulePageSpec:
    page_id: str
    title: str
    factory: Callable[[AppContext], Any]
    order: int = 100

    def __post_init__(self) -> None:
        if not _PAGE_ID_PATTERN.fullmatch(self.page_id.strip()):
            raise ModuleRegistrationError(
                "Page IDs must start with a lowercase letter and contain only "
                "lowercase letters, digits, hyphens or underscores."
            )
        if not self.title.strip():
            raise ModuleRegistrationError(f"Module page '{self.page_id}' requires a title.")


class PlatformModule(Protocol):
    """Lifecycle contract for built-in and installed module packages."""

    def configure(self, context: AppContext) -> None:
        """Register module services and integrations before module startup."""

    def start(self, context: AppContext) -> None:
        """Start background resources after every module has been configured."""

    def stop(self, context: AppContext) -> None:
        """Release resources during orderly application shutdown."""


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    manifest: ModuleManifest
    factory: Callable[[], PlatformModule]
    pages: tuple[ModulePageSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class RegisteredModulePage:
    module_id: str
    page_id: str
    title: str
    factory: Callable[[AppContext], Any]
    order: int

    @property
    def key(self) -> str:
        return f"{self.module_id}.{self.page_id}"


class ModuleRegistry:
    """Module catalogue with API compatibility and deterministic dependency order."""

    def __init__(
        self,
        *,
        api_version: int = PLATFORM_MODULE_API_VERSION,
        entry_point_group: str = MODULE_ENTRY_POINT_GROUP,
    ) -> None:
        if api_version < 1:
            raise ValueError("Platform module API version must be positive.")
        self._api_version = api_version
        self._entry_point_group = entry_point_group
        self._modules: dict[str, ModuleSpec] = {}

    def register(self, spec: ModuleSpec) -> None:
        manifest = spec.manifest
        if not callable(spec.factory):
            raise ModuleRegistrationError(
                f"Module '{manifest.module_id}' requires a callable module factory."
            )
        if manifest.api_version != self._api_version:
            raise ModuleRegistrationError(
                f"Module '{manifest.module_id}' requires API {manifest.api_version}; "
                f"host API is {self._api_version}."
            )
        if manifest.module_id in self._modules:
            raise ModuleRegistrationError(
                f"Module '{manifest.module_id}' is already registered."
            )
        page_ids = [page.page_id for page in spec.pages]
        if len(page_ids) != len(set(page_ids)):
            raise ModuleRegistrationError(
                f"Module '{manifest.module_id}' declares duplicate page IDs."
            )
        self._modules[manifest.module_id] = spec

    def discover_entry_points(
        self,
        enabled_module_ids: Iterable[str] = (),
        *,
        discovered: Iterable[EntryPoint] | None = None,
    ) -> tuple[str, ...]:
        """Load explicitly enabled installed Python modules.

        Entry-point modules execute in the application process. Only trusted
        packages should be installed and enabled. Discovery is opt-in through
        the local application configuration; merely installing a package does
        not execute it.
        """
        enabled = set(enabled_module_ids)
        if not enabled:
            return ()
        available_points = (
            entry_points().select(group=self._entry_point_group)
            if discovered is None
            else tuple(discovered)
        )
        available = {point.name: point for point in available_points}
        unknown = enabled - set(available)
        if unknown:
            raise ModuleRegistrationError(
                "Enabled module packages are not installed: " + ", ".join(sorted(unknown))
            )

        loaded: list[str] = []
        for module_id in sorted(enabled):
            point = available[module_id]
            try:
                provider = point.load()
                spec = provider()
            except Exception as exc:  # noqa: BLE001 - identify the package boundary
                raise ModuleRegistrationError(
                    f"Could not load module entry point '{module_id}': {exc}"
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
            raise ModuleRegistrationError(
                f"Module '{module_id}' is not registered."
            ) from exc

    def all(self) -> tuple[ModuleSpec, ...]:
        return tuple(
            sorted(
                self._modules.values(),
                key=lambda item: (item.manifest.module_id, item.manifest.title),
            )
        )

    def startup_order(self) -> tuple[ModuleSpec, ...]:
        for spec in self._modules.values():
            for dependency in spec.manifest.dependencies:
                if dependency not in self._modules:
                    raise ModuleDependencyError(
                        f"Module '{spec.manifest.module_id}' requires missing "
                        f"module '{dependency}'."
                    )

        ordered: list[ModuleSpec] = []
        visiting: list[str] = []
        visited: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in visited:
                return
            if module_id in visiting:
                cycle = " -> ".join((*visiting, module_id))
                raise ModuleDependencyCycleError(
                    f"Module dependency cycle detected: {cycle}."
                )
            visiting.append(module_id)
            for dependency in self._modules[module_id].manifest.dependencies:
                visit(dependency)
            visiting.pop()
            visited.add(module_id)
            ordered.append(self._modules[module_id])

        for module_id in sorted(self._modules):
            visit(module_id)
        return tuple(ordered)

    def page_specs(self) -> tuple[RegisteredModulePage, ...]:
        pages: list[RegisteredModulePage] = []
        seen: set[str] = set()
        for module in self.startup_order():
            module_id = module.manifest.module_id
            for page in module.pages:
                registered = RegisteredModulePage(
                    module_id=module_id,
                    page_id=page.page_id,
                    title=page.title,
                    factory=page.factory,
                    order=page.order,
                )
                if registered.key in seen:
                    raise ModuleRegistrationError(
                        f"Navigation page '{registered.key}' is registered more than once."
                    )
                seen.add(registered.key)
                pages.append(registered)
        return tuple(sorted(pages, key=lambda item: (item.order, item.module_id, item.page_id)))


class ModuleHost:
    """Owns module instances and guarantees ordered startup and reverse shutdown."""

    def __init__(self, registry: ModuleRegistry, context: AppContext) -> None:
        self._registry = registry
        self._context = context
        self._instances: list[tuple[ModuleSpec, PlatformModule]] = []
        self._started: list[tuple[ModuleSpec, PlatformModule]] = []
        self._attempted = False
        self._stopped = False

    @property
    def started_module_ids(self) -> tuple[str, ...]:
        return tuple(spec.manifest.module_id for spec, _ in self._started)

    def start(self) -> None:
        if self._attempted:
            raise ModuleStartupError("A module host can only be started once.")
        self._attempted = True

        try:
            ordered_specs = self._registry.startup_order()
            for spec in ordered_specs:
                try:
                    instance = spec.factory()
                except Exception as exc:  # noqa: BLE001 - retain module identity
                    raise ModuleStartupError(
                        f"Module '{spec.manifest.module_id}' could not be created: {exc}"
                    ) from exc
                self._validate_instance(spec.manifest.module_id, instance)
                self._instances.append((spec, instance))

            for spec, instance in self._instances:
                try:
                    instance.configure(self._context)
                except Exception as exc:  # noqa: BLE001 - retain module identity
                    raise ModuleStartupError(
                        f"Module '{spec.manifest.module_id}' configuration failed: {exc}"
                    ) from exc

            self._context.services.freeze()

            for spec, instance in self._instances:
                # Register before start so a partially started module is also stopped
                # when its start() method raises.
                self._started.append((spec, instance))
                try:
                    instance.start(self._context)
                except Exception as exc:  # noqa: BLE001 - retain module identity
                    raise ModuleStartupError(
                        f"Module '{spec.manifest.module_id}' startup failed: {exc}"
                    ) from exc
        except Exception:
            self._rollback_startup()
            raise

    def page_specs(self) -> tuple[RegisteredModulePage, ...]:
        if not self._started and self._registry.all():
            raise ModuleHostNotStartedError(
                "Start the module host before building desktop navigation."
            )
        return self._registry.page_specs()

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        failures = self._stop_started()
        if failures:
            details = "; ".join(
                f"{module_id}: {error}" for module_id, error in failures
            )
            raise ModuleShutdownError(f"One or more modules failed to stop: {details}")

    def _rollback_startup(self) -> None:
        failures = self._stop_started()
        for module_id, error in failures:
            self._context.logger.error(
                "Module '%s' failed during startup rollback: %s", module_id, error
            )

    def _stop_started(self) -> list[tuple[str, Exception]]:
        failures: list[tuple[str, Exception]] = []
        for spec, instance in reversed(self._started):
            try:
                instance.stop(self._context)
            except Exception as exc:  # noqa: BLE001 - continue stopping remaining modules
                failures.append((spec.manifest.module_id, exc))
                self._context.logger.exception(
                    "Module '%s' failed during shutdown", spec.manifest.module_id
                )
        self._started.clear()
        return failures

    @staticmethod
    def _validate_instance(module_id: str, instance: object) -> None:
        required = ("configure", "start", "stop")
        missing = [
            name for name in required
            if not callable(getattr(instance, name, None))
        ]
        if missing:
            raise ModuleStartupError(
                f"Module '{module_id}' does not implement lifecycle methods: "
                + ", ".join(missing)
            )
