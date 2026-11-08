from mechpro.core.module_registry import ModuleRegistry, ModuleSpec
from mechpro.modules.sample_module import create_sample_widget


def test_module_registration():
    reg = ModuleRegistry()
    reg.register(ModuleSpec(name="s", title="Sample", factory=create_sample_widget))
    assert len(reg.all()) == 1
    assert reg.all()[0].name == "s"

def test_duplicate_registration():
    reg = ModuleRegistry()
    reg.register(ModuleSpec(name="s", title="Sample", factory=create_sample_widget))
    try:
        reg.register(ModuleSpec(name="s", title="Sample2", factory=create_sample_widget))
        raised = False
    except ValueError:
        raised = True
    assert raised
