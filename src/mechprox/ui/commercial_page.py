from decimal import Decimal
from uuid import UUID

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mechprox.data.project_repository import (
    CommercialAppendError,
    ProjectNotFoundError,
    ProjectRepository,
)
from mechprox.domain.commercial import BOMDocument, BOQDocument
from mechprox.domain.model import EngineeringModel
from mechprox.workflows.takeoff import generate_takeoff


class CommercialPage(QWidget):
    """Project BOM/BOQ generation, traceable line items and currency-separated totals."""

    def __init__(self, repository: ProjectRepository) -> None:
        super().__init__()
        self.repository = repository
        self._model: EngineeringModel | None = None
        layout = QVBoxLayout(self)
        title = QLabel("BOM / BOQ — Metraj ve Maliyet")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "BOM fiziksel ürünleri; BOQ ise ürünlere atanmış poz ve metraj kurallarını "
            "kullanarak iş kalemlerini listeler. Miktarlar proje nesnelerinden türetilir."
        )
        description.setObjectName("mutedText")
        description.setWordWrap(True)
        layout.addWidget(description)

        actions = QHBoxLayout()
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._load_project)
        actions.addWidget(self.project_combo, 1)
        self.generate_button = QPushButton("BOM + BOQ oluştur")
        self.generate_button.setObjectName("primaryButton")
        self.generate_button.clicked.connect(self._generate)
        actions.addWidget(self.generate_button)
        layout.addLayout(actions)

        self.status = QLabel("Proje seçin.")
        self.status.setObjectName("mutedText")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        bom_title = QLabel("BOM — Fiziksel malzeme listesi")
        bom_title.setObjectName("sectionTitle")
        layout.addWidget(bom_title)
        self.bom_table = self._make_table(
            ["Ürün kodu", "Ürün / malzeme", "Miktar", "Birim", "Kaynak nesne adedi"]
        )
        layout.addWidget(self.bom_table, 1)

        boq_title = QLabel("BOQ — Poz bazlı metraj ve keşif")
        boq_title.setObjectName("sectionTitle")
        layout.addWidget(boq_title)
        self.boq_table = self._make_table(
            ["Poz no", "Poz açıklaması", "Miktar", "Birim", "Birim fiyat", "Tutar", "Para birimi"]
        )
        layout.addWidget(self.boq_table, 1)

        self.cost_totals = QLabel("Maliyet toplamları: —")
        self.cost_totals.setObjectName("sectionTitle")
        layout.addWidget(self.cost_totals)
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

    def refresh(self) -> None:
        previous = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for project in self.repository.list():
            self.project_combo.addItem(
                f"{project.project_code} — {project.name}", str(project.id)
            )
        if previous:
            index = self.project_combo.findData(previous)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
        self.project_combo.blockSignals(False)
        self._load_project()

    def _selected_project_id(self) -> UUID | None:
        value = self.project_combo.currentData()
        return UUID(str(value)) if value else None

    def _load_project(self, *_args) -> None:
        project_id = self._selected_project_id()
        self._model = None
        self.bom_table.setRowCount(0)
        self.boq_table.setRowCount(0)
        self.cost_totals.setText("Maliyet toplamları: —")
        self.generate_button.setEnabled(project_id is not None)
        if project_id is None:
            self.status.setText("BOM / BOQ üretmek için proje oluşturun.")
            return
        try:
            self._model = self.repository.get(project_id)
        except ProjectNotFoundError as exc:
            self.status.setText(str(exc))
            return
        if self._model.bom_documents or self._model.boq_documents:
            bom = self._model.bom_documents[-1] if self._model.bom_documents else None
            boq = self._model.boq_documents[-1] if self._model.boq_documents else None
            self._render_documents(self._model, bom, boq)
        else:
            self.status.setText(
                f"{len(self._model.objects)} nesne mevcut. İlk BOM / BOQ belgesini oluşturabilirsiniz."
            )

    def _generate(self) -> None:
        model = self._model
        if model is None:
            return
        try:
            result = generate_takeoff(model, title=f"{model.project.project_code} takeoff")
            if not result.bom.items and not result.boq.items:
                details = "\n".join(result.warnings) or "Ürün atanmış mühendislik nesnesi bulunamadı."
                QMessageBox.information(self, "Metraj oluşturulamadı", details)
                return
            self.repository.append_commercial_documents(model, result.bom, result.boq)
        except (CommercialAppendError, ProjectNotFoundError, ValueError) as exc:
            QMessageBox.warning(self, "BOM / BOQ oluşturulamadı", str(exc))
            return
        self._load_project()
        if result.warnings:
            self.status.setText(
                f"BOM: {len(result.bom.items)} satır · BOQ: {len(result.boq.items)} satır\n"
                + "\n".join(result.warnings)
            )

    def _render_documents(
        self,
        model: EngineeringModel,
        bom: BOMDocument | None,
        boq: BOQDocument | None,
    ) -> None:
        products = {item.id: item for item in model.products}
        positions = {item.id: item for item in model.positions}
        totals: dict[str, Decimal] = {}

        if bom is not None:
            self.bom_table.setRowCount(len(bom.items))
            for row, item in enumerate(bom.items):
                product = products.get(item.product_reference_id)
                values = (
                    product.product_code if product else "Eksik ürün",
                    product.name if product else "Eksik ürün referansı",
                    str(item.quantity.value),
                    item.quantity.unit_code,
                    str(len(item.source_object_ids)),
                )
                self._set_row(self.bom_table, row, values)

        if boq is not None:
            self.boq_table.setRowCount(len(boq.items))
            for row, item in enumerate(boq.items):
                position = positions.get(item.position_reference_id)
                price = position.unit_price if position else None
                currency = position.currency_code if position else None
                amount = (
                    price * item.quantity.value
                    if price is not None and currency is not None
                    else None
                )
                if amount is not None and currency:
                    totals[currency] = totals.get(currency, Decimal(0)) + amount
                values = (
                    position.position_code if position else "Eksik poz",
                    position.name if position else "Eksik poz referansı",
                    str(item.quantity.value),
                    item.quantity.unit_code,
                    f"{price:,.2f}" if price is not None else "—",
                    f"{amount:,.2f}" if amount is not None else "—",
                    currency or "—",
                )
                self._set_row(self.boq_table, row, values)

        if totals:
            total_text = " · ".join(
                f"{currency} {amount:,.2f}" for currency, amount in sorted(totals.items())
            )
        else:
            total_text = "Birim fiyatı tanımlı poz bulunmuyor."
        self.cost_totals.setText(f"Maliyet toplamları: {total_text}")
        self.status.setText(
            f"Son kayıt — BOM: {len(bom.items) if bom else 0} satır · "
            f"BOQ: {len(boq.items) if boq else 0} satır"
        )

    @staticmethod
    def _set_row(table: QTableWidget, row: int, values: tuple[str, ...]) -> None:
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(value))
