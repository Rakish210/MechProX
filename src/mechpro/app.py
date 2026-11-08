import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from mechpro.core.config import ConfigManager
from mechpro.core.context import AppContext, configure_logging
from mechpro.core.module_registry import ModuleRegistry, ModuleSpec
from mechpro.modules.sample_module import create_sample_widget
from mechpro.ui.main_window import MainWindow


def main() -> int:
    logger = configure_logging()
    context = AppContext(config={})
    config = ConfigManager(Path.home() / ".mechpro" / "config.json")
    context.config = config.data

    registry = ModuleRegistry()
    registry.register(ModuleSpec(name="sample", title="Sample Module", factory=create_sample_widget))

    app = QApplication(sys.argv)
    window = MainWindow(context, registry)
    window.show()
    logger.info("Application started")
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
