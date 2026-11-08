from PySide6.QtWidgets import QHBoxLayout, QListWidget, QMainWindow, QStackedWidget, QWidget

from mechpro.core.context import AppContext
from mechpro.core.module_registry import ModuleRegistry


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext, registry: ModuleRegistry) -> None:
        super().__init__()
        self.context = context
        self.registry = registry
        self.setWindowTitle("MechPro - Foundation")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        self.nav = QListWidget()
        self.nav.setFixedWidth(220)
        layout.addWidget(self.nav)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        for spec in registry.all():
            self.nav.addItem(spec.title)
            self.stack.addWidget(spec.factory(context))

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        if self.stack.count() > 0:
            self.nav.setCurrentRow(0)
