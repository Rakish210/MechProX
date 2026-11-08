import pytest

from mechprox.core.service_registry import (
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
    ServiceRegistry,
    ServiceRegistryFrozenError,
)


class ProjectStore:
    pass


class ProjectStoreImplementation(ProjectStore):
    pass


def test_service_registry_resolves_services_by_contract() -> None:
    registry = ServiceRegistry()
    instance = ProjectStoreImplementation()
    registry.register(ProjectStore, instance)

    assert registry.get(ProjectStore) is instance
    assert registry.require(ProjectStore) is instance
    assert registry.registered_contracts() == (ProjectStore,)


def test_service_registry_rejects_duplicate_contracts() -> None:
    registry = ServiceRegistry()
    registry.register(ProjectStore, ProjectStoreImplementation())

    with pytest.raises(ServiceAlreadyRegisteredError, match="already registered"):
        registry.register(ProjectStore, ProjectStoreImplementation())


def test_service_registry_reports_missing_required_service() -> None:
    registry = ServiceRegistry()

    assert registry.get(ProjectStore) is None
    with pytest.raises(ServiceNotFoundError, match="has not been registered"):
        registry.require(ProjectStore)


def test_service_registry_freeze_blocks_late_registration() -> None:
    registry = ServiceRegistry()
    registry.freeze()

    assert registry.is_frozen
    with pytest.raises(ServiceRegistryFrozenError, match="frozen"):
        registry.register(ProjectStore, ProjectStoreImplementation())
