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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mechprox.data.catalogue_repository import CatalogueConflictError, CatalogueRepository
from mechprox.domain.commercial import PositionProductMapping, PositionReference, ProductReference
from mechprox.domain.enums import InformationOrigin


def _required(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} alanı zorunludur.")
    return cleaned


class _CatalogueDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        root_layout = QVBoxLayout(self)
        self.form = QFormLayout()
        root_layout.addLayout(self.form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

    def _validate(self) -> None:
        try:
            self.build()
        except (ValueError, TypeError, InvalidOperation) as exc:
            QMessageBox.warning(self, "Kayıt geçersiz", str(exc))
            return
        self.accept()


class NewProductDialog(_CatalogueDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Yeni fiziksel ürün / malzeme", parent)
        self.catalogue = QLineEdit("USER")
        self.code = QLineEdit()
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.unit = QLineEdit("piece")
        self.manufacturer = QLineEdit()
        self.form.addRow("Katalog kodu *", self.catalogue)
        self.form.addRow("Ürün kodu *", self.code)
        self.form.addRow("Ürün / malzeme adı *", self.name)
        self.form.addRow("Kategori kodu *", self.category)
        self.form.addRow("Birim kodu *", self.unit)
        self.form.addRow("Üretici", self.manufacturer)

    def build(self) -> ProductReference:
        return ProductReference(
            catalogue_code=_required(self.catalogue.text(), "Katalog kodu"),
            product_code=_required(self.code.text(), "Ürün kodu"),
            name=_required(self.name.text(), "Ürün adı"),
            category_code=_required(self.category.text(), "Kategori kodu"),
            unit_code=_required(self.unit.text(), "Birim kodu"),
            manufacturer=self.manufacturer.text().strip() or None,
            origin=InformationOrigin.USER_INPUT,
        )


class NewPositionDialog(_CatalogueDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Yeni BOQ poz kaydı", parent)
        self.catalogue = QLineEdit("USER-BOQ")
        self.code = QLineEdit()
        self.name = QLineEdit()
        self.unit = QLineEdit("piece")
        self.jurisdiction = QLineEdit("TR")
        self.price = QLineEdit()
        self.currency = QComboBox()
        self.currency.addItems(["TRY", "KZT", "USD", "EUR"])
        self.form.addRow("Poz kataloğu *", self.catalogue)
        self.form.addRow("Poz numarası *", self.code)
        self.form.addRow("Poz açıklaması *", self.name)
        self.form.addRow("Birim kodu *", self.unit)
        self.form.addRow("Ülke / mevzuat", self.jurisdiction)
        self.form.addRow("Birim fiyat", self.price)
        self.form.addRow("Para birimi", self.currency)

    def build(self) -> PositionReference:
        raw_price = self.price.text().strip().replace(",", ".")
        price = Decimal(raw_price) if raw_price else None
        if price is not None and not price.is_finite():
            raise ValueError("Birim fiyat sonlu bir sayı olmalıdır.")
        return PositionReference(
            catalogue_code=_required(self.catalogue.text(), "Poz kataloğu"),
            position_code=_required(self.code.text(), "Poz numarası"),
            name=_required(self.name.text(), "Poz açıklaması"),
            unit_code=_required(self.unit.text(), "Birim kodu"),
            jurisdiction=self.jurisdiction.text().strip() or None,
            unit_price=price,
            currency_code=self.currency.currentText() if price is not None else None,
        )


class NewMappingDialog(_CatalogueDialog):
    def __init__(
        self,
        products: tuple[ProductReference, ...],
        positions: tuple[PositionReference, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Poz – ürün eşleştirmesi", parent)
        self.products = products
        self.positions = positions
        self.position = QComboBox()
        self.product = QComboBox()
        for item in positions:
            self.position.addItem(f"{item.position_code} — {item.name}", item.id)
        for item in products:
            self.product.addItem(f"{item.product_code} — {item.name}", item.id)
        self.code = QLineEdit()
        self.version = QLineEdit("1")
        self.rule = QComboBox()
        self.rule.addItems(["LENGTH", "AREA", "VOLUME", "COUNT", "WEIGHT", "MANUAL"])
        self.form.addRow("Poz *", self.position)
        self.form.addRow("Fiziksel ürün *", self.product)
        self.form.addRow("Eşleştirme kodu *", self.code)
        self.form.addRow("Revizyon *", self.version)
        self.form.addRow("Metraj kuralı *", self.rule)

    def build(self) -> PositionProductMapping:
        position_id = self.position.currentData()
        product_id = self.product.currentData()
        if position_id is None or product_id is None:
            raise ValueError("Poz ve ürün seçilmelidir.")
        return PositionProductMapping(
            position_reference_id=UUID(str(position_id)),
            product_reference_id=UUID(str(product_id)),
            mapping_code=_required(self.code.text(), "Eşleştirme kodu"),
            mapping_version=_required(self.version.text(), "Eşleştirme revizyonu"),
            measurement_rule_code=self.rule.currentText(),
        )


class CataloguePage(QWidget):
    """User-manageable product and BOQ-position catalogues with explicit mappings."""

    def __init__(self, repository: CatalogueRepository) -> None:
        super().__init__()
        self.repository = repository
        self._snapshot = repository.export_snapshot()
        layout = QVBoxLayout(self)
        title = QLabel("Ürün ve Poz Kütüphanesi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "Fiziksel ürünleri ve ticari pozları ayrı kataloglarda yönetin; "
            "metraj kurallarıyla sürümlü olarak eşleştirin."
        )
        description.setObjectName("mutedText")
        layout.addWidget(description)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.product_table = self._make_table(
            ["Katalog", "Ürün kodu", "Ürün / malzeme", "Kategori", "Birim", "Üretici"]
        )
        self.position_table = self._make_table(
            ["Katalog", "Poz no", "Poz açıklaması", "Birim", "Bölge", "Birim fiyat"]
        )
        self.mapping_table = self._make_table(
            ["Eşleştirme", "Revizyon", "Poz", "Fiziksel ürün", "Metraj kuralı", "Durum"]
        )
        self.tabs.addTab(self._tab(self.product_table, "＋  Ürün ekle", self._add_product), "Fiziksel Ürünler")
        self.tabs.addTab(self._tab(self.position_table, "＋  Poz ekle", self._add_position), "BOQ Pozları")
        self.tabs.addTab(self._tab(self.mapping_table, "＋  Eşleştirme ekle", self._add_mapping), "Poz – Ürün Eşleştirmeleri")
        self.refresh()

    @staticmethod
    def _make_table(headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for column in range(3, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        return table

    @staticmethod
    def _tab(table: QTableWidget, button_text: str, callback) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        heading = QHBoxLayout()
        heading.addStretch()
        button = QPushButton(button_text)
        button.setObjectName("primaryButton")
        button.clicked.connect(callback)
        heading.addWidget(button)
        layout.addLayout(heading)
        layout.addWidget(table, 1)
        return widget

    def refresh(self) -> None:
        self._snapshot = self.repository.export_snapshot()
        self.product_table.setRowCount(len(self._snapshot.products))
        for row, item in enumerate(self._snapshot.products):
            values = (
                item.catalogue_code, item.product_code, item.name, item.category_code,
                item.unit_code, item.manufacturer or "—",
            )
            self._set_row(self.product_table, row, values, item.id)

        self.position_table.setRowCount(len(self._snapshot.positions))
        for row, item in enumerate(self._snapshot.positions):
            price = (
                f"{item.unit_price:,.2f} {item.currency_code}"
                if item.unit_price is not None and item.currency_code
                else "—"
            )
            values = (
                item.catalogue_code, item.position_code, item.name, item.unit_code,
                item.jurisdiction or "—", price,
            )
            self._set_row(self.position_table, row, values, item.id)

        products = {item.id: item for item in self._snapshot.products}
        positions = {item.id: item for item in self._snapshot.positions}
        self.mapping_table.setRowCount(len(self._snapshot.mappings))
        for row, item in enumerate(self._snapshot.mappings):
            position = positions.get(item.position_reference_id)
            product = products.get(item.product_reference_id)
            values = (
                item.mapping_code, item.mapping_version,
                position.position_code if position else "Eksik poz",
                product.product_code if product else "Eksik ürün",
                item.measurement_rule_code, "Aktif" if item.enabled else "Pasif",
            )
            self._set_row(self.mapping_table, row, values, item.id)

    @staticmethod
    def _set_row(table: QTableWidget, row: int, values: tuple[str, ...], record_id) -> None:
        for column, value in enumerate(values):
            cell = QTableWidgetItem(value)
            if column == 0:
                cell.setData(Qt.ItemDataRole.UserRole, str(record_id))
            table.setItem(row, column, cell)

    def _save_dialog_record(self, dialog: _CatalogueDialog, register) -> None:
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            register(dialog.build())
        except (CatalogueConflictError, ValueError) as exc:
            QMessageBox.warning(self, "Katalog kaydı oluşturulamadı", str(exc))
            return
        self.refresh()

    def _add_product(self) -> None:
        self._save_dialog_record(NewProductDialog(self), self.repository.register_product)

    def _add_position(self) -> None:
        self._save_dialog_record(NewPositionDialog(self), self.repository.register_position)

    def _add_mapping(self) -> None:
        if not self._snapshot.products or not self._snapshot.positions:
            QMessageBox.information(
                self, "Önce katalog kaydı oluşturun",
                "Eşleştirme yapmadan önce en az bir fiziksel ürün ve bir BOQ pozu ekleyin.",
            )
            return
        dialog = NewMappingDialog(self._snapshot.products, self._snapshot.positions, self)
        self._save_dialog_record(dialog, self.repository.register_mapping)
