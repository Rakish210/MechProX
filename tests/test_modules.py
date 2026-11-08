import pytest

from mechpro.core.context import AppContext
from mechpro.core.module_registry import ModuleRegistry, ModuleSpec


def _factory(_: AppContext) -> object:
    return object()


def test_module_registration() -> None:
    registry = ModuleRegistry()
    registry.register(ModuleSpec(name="projects", title="Projects", factory=_factory))

    assert len(registry.all()) == 1
    assert registry.all()[0].name == "projects"


def test_duplicate_registration_is_rejected() -> None:
    registry = ModuleRegistry()
    registry.register(ModuleSpec(name="projects", title="Projects", factory=_factory))

    with pytest.raises(ValueError, match="Module already registered"):
        registry.register(ModuleSpec(name="projects", title="Duplicate", factory=_factory))
