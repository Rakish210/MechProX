from datetime import date

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mechprox.data.source_registry_repository import (
    SourceRegistryConflictError,
    SourceRegistryRepository,
)
from mechprox.domain.base import SourceReference, StandardReference
from mechprox.domain.enums import InformationOrigin, SourceKind


def _required(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} alanı zorunludur.")
    return cleaned


class _SourceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kaynak belgesi kaydı")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.kind = QComboBox()
        for kind in SourceKind:
            self.kind.addItem(kind.value.replace("_", " ").title(), kind)
        self.name = QLineEdit()
        self.revision = QLineEdit()
        self.uri = QLineEdit()
        self.uri.setPlaceholderText("URL, dosya yolu veya belge URI")
        self.entity_id = QLineEdit()
        self.handle = QLineEdit()
        self.unique_id = QLineEdit()
        self.page = QLineEdit()
        self.sheet = QLineEdit()
        self.content_hash = QLineEdit()
        self.origin = QComboBox()
        for origin in InformationOrigin:
            self.origin.addItem(origin.value.replace("_", " ").title(), origin)
        form.addRow("Kaynak türü *", self.kind)
        form.addRow("Belge adı *", self.name)
        form.addRow("Belge revizyonu", self.revision)
        form.addRow("URI / dosya konumu", self.uri)
        form.addRow("Harici varlık ID", self.entity_id)
        form.addRow("DWG entity handle", self.handle)
        form.addRow("BIM UniqueId", self.unique_id)
        form.addRow("Sayfa numarası", self.page)
        form.addRow("Pafta / sayfa adı", self.sheet)
        form.addRow("SHA-256 / içerik özeti", self.content_hash)
        form.addRow("Bilgi kökeni *", self.origin)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def build(self) -> SourceReference:
        kind = self.kind.currentData()
        origin = self.origin.currentData()
        if not isinstance(kind, SourceKind) or not isinstance(origin, InformationOrigin):
            raise ValueError("Kaynak türü ve bilgi kökeni seçilmelidir.")
        page_number = int(self.page.text().strip()) if self.page.text().strip() else None
        uri = self.uri.text().strip() or None
        name = self.name.text().strip() or None
        if not uri and not name:
            raise ValueError("Belge adı veya URI alanlarından en az biri doldurulmalıdır.")
        return SourceReference(
            source_kind=kind,
            document_name=name,
            document_revision=self.revision.text().strip() or None,
            uri=uri,
            external_entity_id=self.entity_id.text().strip() or None,
            entity_handle=self.handle.text().strip() or None,
            element_unique_id=self.unique_id.text().strip() or None,
            page_number=page_number,
            sheet_name=self.sheet.text().strip() or None,
            content_hash=self.content_hash.text().strip() or None,
            origin=origin,
        )

    def _accept_if_valid(self) -> None:
        try:
            self.build()
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Kaynak kaydı geçersiz", str(exc))
            return
        self.accept()


class _StandardDialog(QDialog):
    def __init__(
        self,
        sources: tuple[SourceReference, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Standart / madde kaydı")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.code = QLineEdit()
        self.title = QLineEdit()
        self.edition = QLineEdit()
        self.jurisdiction = QLineEdit()
        self.clause = QLineEdit()
        self.published = QLineEdit()
        self.published.setPlaceholderText("YYYY-MM-DD")
        self.effective_from = QLineEdit()
        self.effective_from.setPlaceholderText("YYYY-MM-DD")
        self.effective_to = QLineEdit()
        self.effective_to.setPlaceholderText("YYYY-MM-DD")
        self.source = QComboBox()
        self.source.addItem("Kaynak belgesi bağlanmadı", None)
        for item in sources:
            label = f"{item.document_name or item.uri or item.id} — {item.document_revision or 'revizyon belirtilmedi'}"
            self.source.addItem(label, str(item.id))
        form.addRow("Standart kodu *", self.code)
        form.addRow("Başlık *", self.title)
        form.addRow("Baskı / edisyon *", self.edition)
        form.addRow("Ülke / yetki alanı", self.jurisdiction)
        form.addRow("Madde / bölüm", self.clause)
        form.addRow("Yayın tarihi", self.published)
        form.addRow("Yürürlük başlangıcı", self.effective_from)
        form.addRow("Yürürlük bitişi", self.effective_to)
        form.addRow("Kaynak belge", self.source)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _optional_date(value: str) -> date | None:
        return date.fromisoformat(value.strip()) if value.strip() else None

    def build(self) -> StandardReference:
        source_id = self.source.currentData()
        return StandardReference(
            standard_code=_required(self.code.text(), "Standart kodu"),
            title=_required(self.title.text(), "Başlık"),
            edition=_required(self.edition.text(), "Baskı / edisyon"),
            jurisdiction=self.jurisdiction.text().strip() or None,
            clause=self.clause.text().strip() or None,
            published_date=self._optional_date(self.published.text()),
            effective_from=self._optional_date(self.effective_from.text()),
            effective_to=self._optional_date(self.effective_to.text()),
            source_reference_id=source_id if source_id else None,
        )

    def _accept_if_valid(self) -> None:
        try:
            self.build()
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Standart kaydı geçersiz", str(exc))
            return
        self.accept()


class SourceRegistryPage(QWidget):
    """Source-document and standard-clause register with provenance links."""

    def __init__(self, repository: SourceRegistryRepository) -> None:
        super().__init__()
        self.repository = repository
        layout = QVBoxLayout(self)
        title = QLabel("Kaynak ve Standart Kütüphanesi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "Teknik dokümanları, standart baskılarını ve madde referanslarını kaydedin. "
            "Standart kayıtları mümkün olduğunda kaynak belgeye bağlanır."
        )
        description.setObjectName("mutedText")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.source_table = self._make_table(
            ["Tür", "Belge adı", "Revizyon", "URI", "Sayfa", "İçerik özeti"]
        )
        self.standard_table = self._make_table(
            ["Kod", "Edisyon", "Yetki alanı", "Madde", "Başlık", "Kaynak"]
        )
        self.tabs.addTab(
            self._tab(self.source_table, "＋  Kaynak ekle", self._add_source),
            "Kaynak Belgeleri",
        )
        self.tabs.addTab(
            self._tab(self.standard_table, "＋  Standart / madde ekle", self._add_standard),
            "Standartlar ve Maddeler",
        )
        self.refresh()

    @staticmethod
    def _make_table(headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        return table

    @staticmethod
    def _tab(table: QTableWidget, button_text: str, callback) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        actions = QHBoxLayout()
        actions.addStretch()
        button = QPushButton(button_text)
        button.setObjectName("primaryButton")
        button.clicked.connect(callback)
        actions.addWidget(button)
        layout.addLayout(actions)
        layout.addWidget(table, 1)
        return widget

    def refresh(self) -> None:
        snapshot = self.repository.export_snapshot()
        sources = {item.id: item for item in snapshot.sources}
        self.source_table.setRowCount(len(snapshot.sources))
        for row, item in enumerate(snapshot.sources):
            values = (
                item.source_kind.value,
                item.document_name or "—",
                item.document_revision or "—",
                item.uri or "—",
                str(item.page_number) if item.page_number else "—",
                item.content_hash or "—",
            )
            self._set_row(self.source_table, row, values, item.id)

        self.standard_table.setRowCount(len(snapshot.standards))
        for row, item in enumerate(snapshot.standards):
            source = sources.get(item.source_reference_id) if item.source_reference_id else None
            values = (
                item.standard_code,
                item.edition,
                item.jurisdiction or "Global",
                item.clause or "—",
                item.title,
                source.document_name if source else "—",
            )
            self._set_row(self.standard_table, row, values, item.id)

    def _add_source(self) -> None:
        dialog = _SourceDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.repository.register_source(dialog.build())
        except ValueError as exc:
            QMessageBox.warning(self, "Kaynak eklenemedi", str(exc))
            return
        self.refresh()

    def _add_standard(self) -> None:
        sources = self.repository.list_sources()
        dialog = _StandardDialog(sources, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.repository.register_standard(dialog.build())
        except (SourceRegistryConflictError, ValueError) as exc:
            QMessageBox.warning(self, "Standart eklenemedi", str(exc))
            return
        self.refresh()

    @staticmethod
    def _set_row(table: QTableWidget, row: int, values: tuple[str, ...], record_id) -> None:
        for column, value in enumerate(values):
            cell = QTableWidgetItem(value)
            if column == 0:
                cell.setData(256, str(record_id))
            table.setItem(row, column, cell)
