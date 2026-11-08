import os

from PySide6.QtWidgets import QApplication

from mechpro.core.context import AppContext
from mechpro.core.module_registry import ModuleRegistry, ModuleSpec
from mechpro.modules.sample_module import create_sample_widget
from mechpro.ui.main_window import MainWindow


def test_main_window_can_be_created_and_shown() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    registry = ModuleRegistry()
    registry.register(
        ModuleSpec(
            name="sample",
            title="Sample Module",
            factory=create_sample_widget,
        )
    )

    window = MainWindow(AppContext(), registry)
    window.show()
    app.processEvents()

    try:
        assert window.isVisible()
        assert window.nav.count() == 1
        assert window.stack.count() == 1
    finally:
        window.close()
