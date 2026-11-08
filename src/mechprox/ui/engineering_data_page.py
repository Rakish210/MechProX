from decimal import Decimal, InvalidOperation
from uuid import UUID

from PySide6.QtWidgets import (
    QComboBox,
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

from mechprox.data.catalogue_repository import CatalogueRepository
from mechprox.data.project_repository import ProjectNotFoundError, ProjectRepository
from mechprox.domain.engineering import Equipment, LinearElement
from mechprox.domain.units import UnitValidationError
from mechprox.workflows.engineering_objects import (
    EngineeringObjectInputError,
    add_equipment,
    add_linear_element,
)


class EngineeringDataPage(QWidget):
    """Project engineering-object entry with explicit product and BOQ mapping assignment."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        catalogue_repository: CatalogueRepository,
    ) -> None:
        super().__init__()
        self.project_repository = project_repository
        self.catalogue_repository = catalogue_repository
        self._products = {}
        self._positions = {}
        self._mappings = {}

        layout = QVBoxLayout(self)
        title = QLabel("Mühendislik Verisi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "Proje nesnelerini oluşturun; her nesneye katalog ürünü ve uygulanacak BOQ "
            "metraj eşleştirmesini açıkça atayın."
        )
        description.setObjectName("mutedText")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._load_project)
        layout.addWidget(self.project_combo)

        form = QFormLayout()
        self.object_type = QComboBox()
        self.object_type.addItem("Doğrusal eleman / boru / kanal", "linear")
        self.object_type.addItem("Ekipman", "equipment")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Örn. Isıtma hattı P-01")
        self.category = QLineEdit("pipe")
        self.discipline = QLineEdit("PLUMBING")
        self.element_type = QLineEdit("pipe")
        self.length = QLineEdit()
        self.length.setPlaceholderText("Örn. 12.5")
        self.unit = QComboBox()
        self.unit.addItems(["meter", "millimeter", "centimeter", "foot"])
        self.product = QComboBox()
        self.mapping = QComboBox()
        self.created_by = QLineEdit("user")
        form.addRow("Nesne türü", self.object_type)
        form.addRow("Nesne adı *", self.name)
        form.addRow("Kategori kodu *", self.category)
        form.addRow("Disiplin kodu *", self.discipline)
        form.addRow("Eleman / ekipman türü *", self.element_type)
        form.addRow("Uzunluk", self.length)
        form.addRow("Uzunluk birimi", self.unit)
        form.addRow("Fiziksel ürün *", self.product)
        form.addRow("BOQ poz eşleştirmesi", self.mapping)
        form.addRow("Kaydı oluşturan *", self.created_by)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.add_button = QPushButton("＋  Mühendislik nesnesi ekle")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self._add_object)
        actions.addWidget(self.add_button)
        self.status = QLabel("Önce proje ve ürün kataloğu oluşturun.")
        self.status.setObjectName("mutedText")
        actions.addWidget(self.status, 1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Nesne", "Tür", "Disiplin", "Fiziksel ürün", "Ölçü", "BOQ poz"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        layout.addWidget(self.table, 1)

        self.object_type.currentIndexChanged.connect(self._object_type_changed)
        self.product.currentIndexChanged.connect(self._product_changed)
        self._load_catalogue()
        self.refresh()

    def _load_catalogue(self) -> None:
        snapshot = self.catalogue_repository.export_snapshot()
        self._products = {item.id: item for item in snapshot.products}
        self._positions = {item.id: item for item in snapshot.positions}
        self._mappings = {item.id: item for item in snapshot.mappings}
        self.product.clear()
        for product in snapshot.products:
            self.product.addItem(
                f"{product.product_code} — {product.name} ({product.unit_code})",
                str(product.id),
            )
        self._product_changed()

    def refresh(self) -> None:
        self._load_catalogue()
        previous = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for project in self.project_repository.list():
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

    def _object_type_changed(self) -> None:
        is_linear = self.object_type.currentData() == "linear"
        self.length.setEnabled(is_linear)
        self.unit.setEnabled(is_linear)
        if not is_linear:
            self.element_type.setText("equipment")

    def _product_changed(self) -> None:
        product_id = self.product.currentData()
        self.mapping.clear()
        self.mapping.addItem("Eşleştirme yok", None)
        if product_id is None:
            return
        for mapping in self._mappings.values():
            if mapping.product_reference_id != UUID(str(product_id)):
                continue
            position = self._positions.get(mapping.position_reference_id)
            if position is not None:
                self.mapping.addItem(
                    f"{position.position_code} — {position.name} "
                    f"[{mapping.measurement_rule_code}, rev {mapping.mapping_version}]",
                    str(mapping.id),
                )

    def _load_project(self, *_args) -> None:
        project_id = self._selected_project_id()
        self.table.setRowCount(0)
        self.add_button.setEnabled(project_id is not None and self.product.count() > 0)
        if project_id is None:
            self.status.setText("Önce bir proje oluşturun.")
            return
        try:
            model = self.project_repository.get(project_id)
        except ProjectNotFoundError as exc:
            self.status.setText(str(exc))
            return
        products = {item.id: item for item in model.products}
        mappings = {item.id: item for item in model.position_product_mappings}
        self.table.setRowCount(len(model.objects))
        for row, obj in enumerate(model.objects):
            product_id = (
                obj.material_product_reference_id
                if isinstance(obj, LinearElement)
                else obj.product_reference_id
                if isinstance(obj, Equipment)
                else None
            )
            product = products.get(product_id) if product_id is not None else None
            quantity = (
                f"{obj.length.value} {obj.length.unit_code}"
                if isinstance(obj, LinearElement)
                else "1 piece"
                if isinstance(obj, Equipment)
                else "—"
            )
            mapping = mappings.get(obj.position_mapping_id) if obj.position_mapping_id else None
            position = (
                next(
                    (item for item in model.positions if item.id == mapping.position_reference_id),
                    None,
                )
                if mapping
                else None
            )
            values = (
                obj.name,
                "Doğrusal" if isinstance(obj, LinearElement) else "Ekipman",
                obj.discipline_code,
                product.product_code if product else "Atanmamış",
                quantity,
                position.position_code if position else "—",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.status.setText(f"{len(model.objects)} mühendislik nesnesi kayıtlı.")

    def _add_object(self) -> None:
        project_id = self._selected_project_id()
        product_value = self.product.currentData()
        if project_id is None or product_value is None:
            QMessageBox.warning(self, "Eksik seçim", "Proje ve fiziksel ürün seçilmelidir.")
            return
        product = self._products.get(UUID(str(product_value)))
        if product is None:
            QMessageBox.warning(self, "Ürün bulunamadı", "Seçilen ürün katalogda bulunamadı.")
            return
        mapping_value = self.mapping.currentData()
        mapping = self._mappings.get(UUID(str(mapping_value))) if mapping_value else None
        position = (
            self._positions.get(mapping.position_reference_id) if mapping is not None else None
        )
        try:
            model = self.project_repository.get(project_id)
            common = {
                "name": self.name.text(),
                "category_code": self.category.text(),
                "discipline_code": self.discipline.text(),
                "product": product,
                "mapping": mapping,
                "position": position,
                "changed_by": self.created_by.text(),
            }
            if self.object_type.currentData() == "linear":
                length_value = Decimal(self.length.text().strip().replace(",", "."))
                updated = add_linear_element(
                    model,
                    element_type=self.element_type.text(),
                    length_value=length_value,
                    length_unit=self.unit.currentText(),
                    **common,
                )
            else:
                updated = add_equipment(
                    model,
                    equipment_type=self.element_type.text() or "equipment",
                    **common,
                )
            self.project_repository.save(updated)
        except (InvalidOperation, ValueError, TypeError, ProjectNotFoundError,
                EngineeringObjectInputError, UnitValidationError) as exc:
            QMessageBox.warning(self, "Nesne kaydedilemedi", str(exc))
            return
        self.name.clear()
        self.length.clear()
        self._load_project()
