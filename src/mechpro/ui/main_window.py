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

from mechpro.calculations.runner import CalculationRunner
from mechpro.core.context import AppContext
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import ProjectRepository
from mechpro.ui.gas_demand_page import GasDemandPage
from mechpro.ui.parameter_registry_page import ParameterRegistryPage
from mechpro.ui.project_page import ComingSoonPage, DashboardPage, ProjectPage


class MainWindow(QMainWindow):
    NAVIGATION = (
        ("Genel Bakış", "dashboard"),
        ("Projeler", "projects"),
        ("Mühendislik Verisi", "engineering"),
        ("Hesaplamalar", "calculations"),
        ("Parametre Kütüphanesi", "parameters"),
        ("Ürün ve Poz Kütüphanesi", "library"),
        ("BOM / BOQ", "commercial"),
        ("CAD / BIM", "cad"),
        ("Raporlar", "reports"),
        ("Ayarlar", "settings"),
    )

    def __init__(
        self,
        context: AppContext,
        repository: ProjectRepository,
        parameter_repository: ParameterRegistryRepository,
        calculation_runner: CalculationRunner,
    ) -> None:
        super().__init__()
        self.context = context
        self.repository = repository
        self.parameter_repository = parameter_repository
        self.setWindowTitle("MechPro — Uzman Mekanik Tesisat Mühendisliği Platformu")
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
        brand = QLabel("MechPro")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)
        tagline = QLabel("ENGINEERING PLATFORM")
        tagline.setObjectName("brandTagline")
        side_layout.addWidget(tagline)
        side_layout.addSpacing(26)

        self.nav = QListWidget()
        self.nav.setObjectName("navigation")
        self.nav.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for title, _ in self.NAVIGATION:
            self.nav.addItem(title)
        side_layout.addWidget(self.nav, 1)
        version = QLabel("LOCAL WORKSPACE  ·  v0.2")
        version.setObjectName("brandTagline")
        side_layout.addWidget(version)
        root.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 24, 30, 24)
        content_layout.setSpacing(18)
        header = QHBoxLayout()
        self.section_title = QLabel("Genel Bakış")
        self.section_title.setObjectName("sectionTitle")
        header.addWidget(self.section_title)
        header.addStretch()
        self.status_label = QLabel("Yerel veritabanı")
        self.status_label.setObjectName("statusPill")
        header.addWidget(self.status_label)
        content_layout.addLayout(header)

        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(repository)
        self.projects = ProjectPage(repository)
        self.parameters = ParameterRegistryPage(parameter_repository)
        self.calculations = GasDemandPage(repository, calculation_runner)
        pages = (
            self.dashboard,
            self.projects,
            ComingSoonPage(
                "Mühendislik Verisi",
                "Ortak mühendislik veri modeli hazır. Nesne ve sistem düzenleyicisi sonraki geliştirme adımında eklenecek.",
            ),
            self.calculations,
            self.parameters,
            ComingSoonPage(
                "Ürün ve Poz Kütüphanesi",
                "Ürün katalogları, üretici verileri, standartlar ve kamu pozları için bilgi kayıt alanı.",
            ),
            ComingSoonPage(
                "BOM / BOQ",
                "Fiziksel malzeme listesi (BOM) ve poz bazlı metraj/keşif (BOQ) ayrı iş akışları olarak geliştirilecek.",
            ),
            ComingSoonPage(
                "CAD / BIM",
                "AutoCAD ve Revit kendi uygulamalarında çalışacak; MechPro köprüler üzerinden veri alışverişi yapacak.",
            ),
            ComingSoonPage("Raporlar", "Hesap raporları, metraj dökümleri ve proje teslim dokümanları."),
            ComingSoonPage(
                "Ayarlar",
                "Yerel çalışma alanı, yedekleme ve entegrasyon ayarları.",
            ),
        )
        for page in pages:
            self.stack.addWidget(page)
        content_layout.addWidget(self.stack, 1)
        root.addWidget(content, 1)

        self.nav.currentRowChanged.connect(self._navigate)
        self.nav.setCurrentRow(0)
        self.setStyleSheet(self._stylesheet())

    def _navigate(self, index: int) -> None:
        if index < 0 or index >= self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        self.section_title.setText(self.NAVIGATION[index][0])
        self.dashboard.refresh()
        self.projects.refresh()
        if index == 3:
            self.calculations.refresh()
        elif index == 4:
            self.parameters.refresh()

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
        QLabel#sectionTitle { font-size: 17pt; font-weight: 650; color: #172334; }
        QLabel#pageTitle { font-size: 22pt; font-weight: 650; color: #172334; }
        QLabel#mutedText { color: #66758a; font-size: 10pt; }
        QLabel#statusPill { background: #e5edf6; color: #34516f; padding: 7px 12px; border-radius: 12px; }
        QLabel#metricValue { font-size: 27pt; font-weight: 700; color: #1c5d91; }
        QLabel#sectionTitle { font-size: 16pt; font-weight: 650; color: #172334; }
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
