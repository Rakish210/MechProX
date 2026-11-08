from datetime import UTC

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mechpro.data.project_repository import (
    ProjectAlreadyExistsError,
    ProjectRepository,
    ProjectSummary,
)
from mechpro.domain.model import EngineeringModel
from mechpro.domain.project import Project


class NewProjectDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Yeni mühendislik projesi")
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.code = QLineEdit()
        self.code.setPlaceholderText("Örn. MP-2026-001")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Proje adı")
        self.client = QLineEdit()
        self.description = QPlainTextEdit()
        self.description.setMaximumHeight(90)
        form.addRow("Proje kodu *", self.code)
        form.addRow("Proje adı *", self.name)
        form.addRow("İşveren", self.client)
        form.addRow("Açıklama", self.description)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        if not self.code.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Eksik bilgi", "Proje kodu ve proje adı zorunludur.")
            return
        self.accept()

    def build_model(self) -> EngineeringModel:
        project = Project(
            project_code=self.code.text().strip(),
            name=self.name.text().strip(),
            client_name=self.client.text().strip() or None,
            description=self.description.toPlainText().strip() or None,
        )
        return EngineeringModel(project=project)


class ProjectPage(QWidget):
    def __init__(self, repository: ProjectRepository) -> None:
        super().__init__()
        self.repository = repository
        layout = QVBoxLayout(self)
        heading = QHBoxLayout()
        title = QLabel("Projeler")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        heading.addStretch()
        self.new_button = QPushButton("＋  Yeni proje")
        self.new_button.setObjectName("primaryButton")
        self.new_button.clicked.connect(self._create_project)
        heading.addWidget(self.new_button)
        layout.addLayout(heading)

        self.description = QLabel(
            "Mühendislik projelerinizi oluşturun ve ortak proje veri modelini yönetin."
        )
        self.description.setObjectName("mutedText")
        layout.addWidget(self.description)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Proje kodu", "Proje adı", "Şema", "Son kayıt"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)
        self.refresh()

    def refresh(self) -> tuple[ProjectSummary, ...]:
        projects = self.repository.list()
        self.table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            values = (
                project.project_code,
                project.name,
                project.schema_version,
                project.updated_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, str(project.id))
                self.table.setItem(row, column, item)
        return projects

    def _create_project(self) -> None:
        dialog = NewProjectDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.repository.create(dialog.build_model())
        except ProjectAlreadyExistsError as exc:
            QMessageBox.warning(self, "Proje kodu kullanılıyor", str(exc))
            return
        self.refresh()


class DashboardPage(QWidget):
    def __init__(self, repository: ProjectRepository) -> None:
        super().__init__()
        self.repository = repository
        layout = QVBoxLayout(self)
        title = QLabel("Mühendislik Kontrol Merkezi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Projeler, mühendislik verisi, hesaplamalar ve ticari çıktılar için merkezi çalışma alanı."
        )
        subtitle.setObjectName("mutedText")
        layout.addWidget(subtitle)

        self.project_count = QLabel("0")
        self.project_count.setObjectName("metricValue")
        metric_label = QLabel("Kayıtlı proje")
        metric_label.setObjectName("mutedText")
        metric_layout = QVBoxLayout()
        metric_layout.addWidget(self.project_count)
        metric_layout.addWidget(metric_label)
        metric_card = QWidget()
        metric_card.setObjectName("metricCard")
        metric_card.setLayout(metric_layout)
        metric_card.setMaximumWidth(240)
        layout.addWidget(metric_card)
        layout.addStretch()

    def refresh(self) -> None:
        self.project_count.setText(str(len(self.repository.list())))


class ComingSoonPage(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)
        detail = QLabel(description)
        detail.setObjectName("mutedText")
        detail.setWordWrap(True)
        layout.addWidget(detail)
        layout.addStretch()
