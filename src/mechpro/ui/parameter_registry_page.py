from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from PySide6.QtCore import Qt
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
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from mechpro.data.parameter_registry_repository import (
    ParameterAlreadyExistsError,
    ParameterRegistryRepository,
)
from mechpro.domain.base import Quantity, QuantityValue, ScalarValue
from mechpro.domain.enums import InformationOrigin
from mechpro.domain.parameters import (
    ParameterDefinition,
    ParameterRevision,
    ParameterRevisionStatus,
    ParameterScopeKind,
    ParameterValueKind,
)


class NewParameterDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Yeni parametre tanımı")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.code = QLineEdit()
        self.name = QLineEdit()
        self.discipline = QLineEdit()
        self.category = QLineEdit()
        self.value_kind = QComboBox()
        self.value_kind.addItem("Skaler değer", ParameterValueKind.SCALAR)
        self.value_kind.addItem("Birimli fiziksel büyüklük", ParameterValueKind.QUANTITY)
        self.dimension = QLineEdit()
        self.dimension.setPlaceholderText("Örn. [pressure], [length]")
        self.unit = QLineEdit()
        self.unit.setPlaceholderText("Örn. bar, meter, watt")

        form.addRow("Parametre kodu *", self.code)
        form.addRow("Parametre adı *", self.name)
        form.addRow("Disiplin kodu *", self.discipline)
        form.addRow("Kategori kodu *", self.category)
        form.addRow("Değer tipi *", self.value_kind)
        form.addRow("Boyut *", self.dimension)
        form.addRow("Kanonik birim *", self.unit)
        layout.addLayout(form)
        self.value_kind.currentIndexChanged.connect(self._update_quantity_fields)
        self._update_quantity_fields()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_quantity_fields(self) -> None:
        is_quantity = self.value_kind.currentData() == ParameterValueKind.QUANTITY
        self.dimension.setEnabled(is_quantity)
        self.unit.setEnabled(is_quantity)

    def build_definition(self) -> ParameterDefinition:
        value_kind = self.value_kind.currentData()
        if not isinstance(value_kind, ParameterValueKind):
            raise ValueError("A parameter value type must be selected.")
        return ParameterDefinition(
            code=self.code.text().strip(),
            name=self.name.text().strip(),
            discipline_code=self.discipline.text().strip(),
            category_code=self.category.text().strip(),
            value_kind=value_kind,
            expected_dimension=self.dimension.text().strip() or None,
            canonical_unit_code=self.unit.text().strip() or None,
        )

    def _accept_if_valid(self) -> None:
        try:
            self.build_definition()
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Parametre tanımı geçersiz", str(exc))
            return
        self.accept()


class NewParameterRevisionDialog(QDialog):
    def __init__(
        self,
        definition: ParameterDefinition,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.definition = definition
        self.setWindowTitle(f"Yeni parametre revizyonu — {definition.code}")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.revision_code = QLineEdit("A")
        self.value = QLineEdit()
        self.unit = QLineEdit(definition.canonical_unit_code or "")
        self.unit.setEnabled(definition.value_kind == ParameterValueKind.QUANTITY)
        self.scope_kind = QComboBox()
        self.scope_kind.addItem("Global", ParameterScopeKind.GLOBAL)
        self.scope_kind.addItem("Ülke / mevzuat alanı", ParameterScopeKind.JURISDICTION)
        self.scope_kind.addItem("Proje", ParameterScopeKind.PROJECT)
        self.scope_key = QLineEdit()
        self.scope_key.setPlaceholderText("Ülke kodu veya proje UUID")
        self.status = QComboBox()
        self.status.addItem("Taslak", ParameterRevisionStatus.DRAFT)
        self.status.addItem("Onaylı", ParameterRevisionStatus.APPROVED)
        self.origin = QComboBox()
        for origin in InformationOrigin:
            self.origin.addItem(origin.value.replace("_", " ").title(), origin)
        self.created_by = QLineEdit()
        self.approved_by = QLineEdit()
        self.valid_from = QLineEdit()
        self.valid_from.setPlaceholderText("YYYY-MM-DD — isteğe bağlı")
        self.valid_to = QLineEdit()
        self.valid_to.setPlaceholderText("YYYY-MM-DD — isteğe bağlı")
        self.change_summary = QLineEdit()

        form.addRow("Revizyon kodu *", self.revision_code)
        form.addRow("Değer *", self.value)
        form.addRow("Birim *", self.unit)
        form.addRow("Kapsam *", self.scope_kind)
        form.addRow("Kapsam anahtarı", self.scope_key)
        form.addRow("Durum *", self.status)
        form.addRow("Bilgi kaynağı *", self.origin)
        form.addRow("Oluşturan *", self.created_by)
        form.addRow("Onaylayan", self.approved_by)
        form.addRow("Geçerlilik başlangıcı", self.valid_from)
        form.addRow("Geçerlilik bitişi", self.valid_to)
        form.addRow("Değişiklik açıklaması", self.change_summary)
        layout.addLayout(form)

        self.scope_kind.currentIndexChanged.connect(self._update_scope_fields)
        self.status.currentIndexChanged.connect(self._update_approval_fields)
        self._update_scope_fields()
        self._update_approval_fields()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_scope_fields(self) -> None:
        scope = self.scope_kind.currentData()
        self.scope_key.setEnabled(scope != ParameterScopeKind.GLOBAL)
        if scope == ParameterScopeKind.GLOBAL:
            self.scope_key.clear()
        elif scope == ParameterScopeKind.JURISDICTION:
            self.scope_key.setPlaceholderText("Örn. KZ, TR")
        else:
            self.scope_key.setPlaceholderText("Proje UUID")

    def _update_approval_fields(self) -> None:
        is_approved = self.status.currentData() == ParameterRevisionStatus.APPROVED
        self.approved_by.setEnabled(is_approved)

    @staticmethod
    def _parse_optional_date(value: str) -> date | None:
        cleaned = value.strip()
        return date.fromisoformat(cleaned) if cleaned else None

    def build_revision(self) -> ParameterRevision:
        scope = self.scope_kind.currentData()
        status = self.status.currentData()
        origin = self.origin.currentData()
        if not isinstance(scope, ParameterScopeKind):
            raise ValueError("A parameter scope must be selected.")
        if not isinstance(status, ParameterRevisionStatus):
            raise ValueError("A revision status must be selected.")
        if not isinstance(origin, InformationOrigin):
            raise ValueError("An information origin must be selected.")

        if self.definition.value_kind == ParameterValueKind.QUANTITY:
            magnitude = Decimal(self.value.text().strip())
            if not magnitude.is_finite():
                raise ValueError("Parameter value must be finite.")
            value = QuantityValue(
                quantity=Quantity(
                    value=magnitude,
                    unit_code=self.unit.text().strip(),
                )
            )
        else:
            raw_value = self.value.text().strip()
            if not raw_value:
                raise ValueError("A scalar parameter value is required.")
            try:
                scalar_value: str | Decimal = Decimal(raw_value)
            except InvalidOperation:
                scalar_value = raw_value
            if isinstance(scalar_value, Decimal) and not scalar_value.is_finite():
                raise ValueError("Parameter value must be finite.")
            value = ScalarValue(value=scalar_value)

        scope_key = self.scope_key.text().strip() if scope != ParameterScopeKind.GLOBAL else ""
        if scope == ParameterScopeKind.PROJECT:
            UUID(scope_key)

        return ParameterRevision(
            definition_id=self.definition.id,
            revision_code=self.revision_code.text().strip(),
            value=value,
            scope_kind=scope,
            scope_key=scope_key,
            status=status,
            valid_from=self._parse_optional_date(self.valid_from.text()),
            valid_to=self._parse_optional_date(self.valid_to.text()),
            origin=origin,
            created_by=self.created_by.text().strip(),
            approved_by=self.approved_by.text().strip() or None,
            change_summary=self.change_summary.text().strip() or None,
        )

    def _accept_if_valid(self) -> None:
        try:
            self.build_revision()
        except (ValueError, TypeError, InvalidOperation) as exc:
            QMessageBox.warning(self, "Parametre revizyonu geçersiz", str(exc))
            return
        self.accept()


class ParameterRegistryPage(QWidget):
    def __init__(self, repository: ParameterRegistryRepository) -> None:
        super().__init__()
        self.repository = repository
        self._definitions: dict[str, ParameterDefinition] = {}

        layout = QVBoxLayout(self)
        heading = QHBoxLayout()
        title = QLabel("Parametre Kütüphanesi")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        heading.addStretch()

        self.add_revision_button = QPushButton("＋  Revizyon ekle")
        self.add_revision_button.setObjectName("secondaryButton")
        self.add_revision_button.setEnabled(False)
        self.add_revision_button.clicked.connect(self._add_revision)
        heading.addWidget(self.add_revision_button)

        self.new_button = QPushButton("＋  Parametre tanımla")
        self.new_button.setObjectName("primaryButton")
        self.new_button.clicked.connect(self._create_definition)
        heading.addWidget(self.new_button)
        layout.addLayout(heading)

        description = QLabel(
            "Mühendislik katsayıları, tasarım limitleri ve teknik girdileri kaynaklı ve sürümlü olarak yönetin."
        )
        description.setObjectName("mutedText")
        layout.addWidget(description)

        self.definition_table = QTableWidget(0, 6)
        self.definition_table.setHorizontalHeaderLabels(
            ["Kod", "Parametre", "Disiplin", "Kategori", "Değer tipi", "Kanonik birim"]
        )
        self._configure_table(self.definition_table)
        self.definition_table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.definition_table, 3)

        history_title = QLabel("Revizyon geçmişi")
        history_title.setObjectName("sectionTitle")
        layout.addWidget(history_title)
        self.revision_table = QTableWidget(0, 6)
        self.revision_table.setHorizontalHeaderLabels(
            ["Revizyon", "Kapsam", "Durum", "Değer", "Geçerli olduğu tarih", "Kaynak"]
        )
        self._configure_table(self.revision_table)
        layout.addWidget(self.revision_table, 2)
        self.refresh()

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )

    def refresh(self, select_definition_id: UUID | None = None) -> None:
        snapshot = self.repository.export_snapshot()
        self._definitions = {str(item.id): item for item in snapshot.definitions}
        self.definition_table.setRowCount(len(snapshot.definitions))
        for row, definition in enumerate(snapshot.definitions):
            values = (
                definition.code,
                definition.name,
                definition.discipline_code,
                definition.category_code,
                definition.value_kind.value,
                definition.canonical_unit_code or "—",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, str(definition.id))
                self.definition_table.setItem(row, column, item)

        if select_definition_id is not None:
            target = str(select_definition_id)
            for row in range(self.definition_table.rowCount()):
                item = self.definition_table.item(row, 0)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) == target:
                    self.definition_table.selectRow(row)
                    break
        elif self.definition_table.rowCount() and not self.definition_table.selectedItems():
            self.definition_table.selectRow(0)

        self._selection_changed(snapshot.revisions)

    def _selected_definition(self) -> ParameterDefinition | None:
        row = self.definition_table.currentRow()
        if row < 0:
            return None
        item = self.definition_table.item(row, 0)
        if item is None:
            return None
        return self._definitions.get(str(item.data(Qt.ItemDataRole.UserRole)))

    def _selection_changed(self, revisions=None) -> None:
        definition = self._selected_definition()
        self.add_revision_button.setEnabled(definition is not None)
        if definition is None:
            self.revision_table.setRowCount(0)
            return

        if revisions is None:
            revisions = self.repository.export_snapshot().revisions
        selected = [item for item in revisions if item.definition_id == definition.id]
        self.revision_table.setRowCount(len(selected))
        for row, revision in enumerate(selected):
            if isinstance(revision.value, QuantityValue):
                value_text = (
                    f"{revision.value.quantity.value} {revision.value.quantity.unit_code}"
                )
            elif isinstance(revision.value, ScalarValue):
                value_text = str(revision.value.value)
            else:
                value_text = "—"
            values = (
                revision.revision_code,
                f"{revision.scope_kind.value}: {revision.scope_key or '—'}",
                revision.status.value,
                value_text,
                f"{revision.valid_from or '—'} / {revision.valid_to or '—'}",
                revision.origin.value,
            )
            for column, value in enumerate(values):
                self.revision_table.setItem(row, column, QTableWidgetItem(value))

    def _create_definition(self) -> None:
        dialog = NewParameterDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            definition = dialog.build_definition()
            self.repository.register_definition(definition)
        except (ParameterAlreadyExistsError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Parametre kaydedilemedi", str(exc))
            return
        self.refresh(select_definition_id=definition.id)

    def _add_revision(self) -> None:
        definition = self._selected_definition()
        if definition is None:
            return
        dialog = NewParameterRevisionDialog(definition, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            revision = dialog.build_revision()
            self.repository.add_revision(revision)
        except (IntegrityError, ValueError, TypeError, InvalidOperation) as exc:
            QMessageBox.warning(self, "Revizyon kaydedilemedi", str(exc))
            return
        self.refresh(select_definition_id=definition.id)
