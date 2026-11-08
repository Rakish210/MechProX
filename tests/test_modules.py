import pytest

from mechpro.core.module_registry import ModuleRegistry, ModuleSpec


def test_module_registration() -> None:
    registry = ModuleRegistry()
    registry.register(ModuleSpec(name="projects", title="Projects", factory=lambda _: object()))

    assert len(registry.all()) == 1
    assert registry.all()[0].name == "projects"


def test_duplicate_registration_is_rejected() -> None:
    registry = ModuleRegistry()
    factory = lambda _: object()
    registry.register(ModuleSpec(name="projects", title="Projects", factory=factory))

    with pytest.raises(ValueError, match="Module already registered"):
        registry.register(ModuleSpec(name="projects", title="Duplicate", factory=factory))
