from __future__ import annotations

from typing import TypeVar, cast


T = TypeVar("T")


class ServiceRegistryError(RuntimeError):
    """Base error for application service registration and lookup."""


class ServiceAlreadyRegisteredError(ServiceRegistryError):
    """Raised when a service contract is registered more than once."""


class ServiceNotFoundError(ServiceRegistryError):
    """Raised when a required application service is unavailable."""


class ServiceRegistryFrozenError(ServiceRegistryError):
    """Raised when services are modified after application composition."""


class ServiceRegistry:
    """Small typed dependency container shared by modules and application workflows."""

    def __init__(self) -> None:
        self._services: dict[type[object], object] = {}
        self._frozen = False

    def register(self, contract: type[T], service: T) -> None:
        if not isinstance(contract, type):
            raise TypeError("A service contract must be a type.")
        if self._frozen:
            raise ServiceRegistryFrozenError(
                "Application services are frozen after module configuration."
            )
        if contract in self._services:
            raise ServiceAlreadyRegisteredError(
                f"Service contract '{contract.__module__}.{contract.__qualname__}' "
                "is already registered."
            )
        self._services[contract] = service

    def get(self, contract: type[T]) -> T | None:
        service = self._services.get(contract)
        return cast(T | None, service)

    def require(self, contract: type[T]) -> T:
        service = self.get(contract)
        if service is None:
            raise ServiceNotFoundError(
                f"Required service '{contract.__module__}.{contract.__qualname__}' "
                "has not been registered."
            )
        return service

    def freeze(self) -> None:
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def registered_contracts(self) -> tuple[type[object], ...]:
        return tuple(self._services)
