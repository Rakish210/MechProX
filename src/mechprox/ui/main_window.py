from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from mechprox.core.context import AppContext
from mechprox.core.module_registry import ModuleHost, RegisteredModulePage


class MainWindow(QMainWindow):
    """Application shell. Navigation is composed entirely from installed modules."""

    def __init__(self, context: AppContext, module_host: ModuleHost) -> None:
        super().__init__()
        self.context = context
        self.module_host = module_host
        self._page_specs: tuple[RegisteredModulePage, ...] = module_host.page_specs()
        if not self._page_specs:
            raise RuntimeError("No module pages were registered; cannot build the workspace.")

        self.setWindowTitle("MechProX — Uzman Mekanik Tesisat Mühendisliği Platformu")
        self.resize(1280, 800)
        self.setMinimumSize(980, 640)

        central = QWidget()
        central.setObjectName("appRoot")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 22, 14, 18)
        self.brand_label = QLabel("MechProX")
        self.brand_label.setObjectName("brand")
        side_layout.addWidget(self.brand_label)
        tagline = QLabel("ENGINEERING PLATFORM")
        tagline.setObjectName("brandTagline")
        side_layout.addWidget(tagline)
        side_layout.addSpacing(26)

        self.nav = QListWidget()
        self.nav.setObjectName("navigation")
        self.nav.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        side_layout.addWidget(self.nav, 1)
        version = QLabel("LOCAL WORKSPACE  ·  MODULAR")
        version.setObjectName("brandTagline")
        side_layout.addWidget(version)
        root.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 24, 30, 24)
        content_layout.setSpacing(18)
        header = QHBoxLayout()
        self.section_title = QLabel("")
        self.section_title.setObjectName("sectionTitle")
        header.addWidget(self.section_title)
        header.addStretch()
        self.status_label = QLabel("Yerel veritabanı")
        self.status_label.setObjectName("statusPill")
        header.addWidget(self.status_label)
        content_layout.addLayout(header)

        self.stack = QStackedWidget()
        self._pages: list[QWidget] = []
        for page_spec in self._page_specs:
            page = page_spec.factory(context)
            if not isinstance(page, QWidget):
                raise TypeError(
                    f"Module page '{page_spec.key}' did not create a QWidget."
                )
            self.nav.addItem(page_spec.title)
            self.stack.addWidget(page)
            self._pages.append(page)

        content_layout.addWidget(self.stack, 1)
        root.addWidget(content, 1)

        self.nav.currentRowChanged.connect(self._navigate)
        self.nav.setCurrentRow(0)
        self.setStyleSheet(self._stylesheet())

    def _navigate(self, index: int) -> None:
        if index < 0 or index >= len(self._pages):
            return
        self.stack.setCurrentIndex(index)
        self.section_title.setText(self._page_specs[index].title)
        page = self._pages[index]
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            try:
                refresh()
                self.status_label.setText("Yerel veritabanı")
            except Exception as exc:  # noqa: BLE001 - isolate page refresh failures
                self.context.logger.exception(
                    "Module page '%s' failed to refresh",
                    self._page_specs[index].key,
                )
                self.status_label.setText("Modül yenileme hatası")
                self.context.logger.error("%s", exc)

    @staticmethod
    def _stylesheet() -> str:
        return """
        QWidget#appRoot { background: #f4f6f9; color: #202938; font-family: "Segoe UI"; font-size: 10pt; }
        QWidget#sidebar { background: #172334; color: #edf2f7; }
        QLabel#brand { color: #ffffff; font-size: 23pt; font-weight: 700; }
        QLabel#brandTagline { color: #91a0b4; font-size: 8pt; letter-spacing: 1px; }
        QListWidget#navigation { border: 0; background: transparent; color: #cbd5e1; outline: 0; }
        QListWidget#navigation::item { padding: 12px 10px; border-radius: 6px; margin: 2px 0; }
        QListWidget#navigation::item:selected { background: #2b405b; color: white; font-weight: 600; }
        QLabel#sectionTitle { font-size: 16pt; font-weight: 650; color: #172334; }
        QLabel#pageTitle { font-size: 22pt; font-weight: 650; color: #172334; }
        QLabel#mutedText { color: #66758a; font-size: 10pt; }
        QLabel#statusPill { background: #e5edf6; color: #34516f; padding: 7px 12px; border-radius: 12px; }
        QLabel#metricValue { font-size: 27pt; font-weight: 700; color: #1c5d91; }
        QWidget#metricCard { background: white; border: 1px solid #e0e6ed; border-radius: 9px; padding: 16px; }
        QPushButton#primaryButton { background: #1e659b; color: white; border: 0; border-radius: 6px; padding: 10px 16px; font-weight: 600; }
        QPushButton#primaryButton:hover { background: #185580; }
        QPushButton#secondaryButton { background: #e5edf6; color: #34516f; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 16px; font-weight: 600; }
        QPushButton#secondaryButton:hover { background: #d8e4f0; }
        QTableWidget { background: white; border: 1px solid #e0e6ed; border-radius: 8px; gridline-color: #edf0f4; }
        QHeaderView::section { background: #edf1f5; color: #44546a; border: 0; padding: 10px; font-weight: 600; }
        QTableWidget::item { padding: 8px; }
        QLineEdit, QPlainTextEdit, QComboBox { background: white; border: 1px solid #cbd5e1; border-radius: 5px; padding: 7px; }
        """
