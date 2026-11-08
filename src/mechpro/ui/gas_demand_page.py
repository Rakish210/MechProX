from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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

from mechpro.calculations.contracts import CalculationRequest
from mechpro.calculations.runner import CalculationPreconditionError, CalculationRunner
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import (
    CalculationAppendError,
    ProjectNotFoundError,
    ProjectRepository,
)
from mechpro.domain.base import QuantityValue
from mechpro.domain.engineering import Equipment
from mechpro.domain.enums import CalculationPurpose, CalculationState
from mechpro.domain.units import UnitValidationError
from mechpro.engines.gas.workflow import GasApplianceInputError, add_gas_appliance


class GasDemandPage(QWidget):
    """Desktop workflow for adding gas appliances and running reference demand."""

    PARAMETER_CODE = "GAS.LOWER_HEATING_VALUE"

    def __init__(
        self,
        project_repository: ProjectRepository,
        parameter_repository: ParameterRegistryRepository,
        calculation_runner: CalculationRunner,
    ) -> None:
        super().__init__()
        self.project_repository = project_repository
        self.parameter_repository = parameter_repository
        self.calculation_runner = calculation_runner

        layout = QVBoxLayout(self)
        title = QLabel("Doğalgaz — Cihaz Debisi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "Cihazların ısıl gücünden, Parametre Kütüphanesi'nde onaylanmış alt ısıl değer "
            "kullanılarak referans gaz debisini hesaplar. Boru çapı ve basınç kaybı hesabı değildir."
        )
        description.setObjectName("mutedText")
        description.setWordWrap(True)
        layout.addWidget(description)

        project_form = QFormLayout()
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._load_selected_project)
        project_form.addRow("Proje", self.project_combo)
        layout.addLayout(project_form)

        appliance_form = QHBoxLayout()
        self.appliance_name = QLineEdit()
        self.appliance_name.setPlaceholderText("Cihaz adı")
        self.appliance_power = QLineEdit()
        self.appliance_power.setPlaceholderText("Örn. 60")
        self.appliance_power.setMaximumWidth(140)
        self.add_appliance_button = QPushButton("Cihaz ekle")
        self.add_appliance_button.setObjectName("secondaryButton")
        self.add_appliance_button.clicked.connect(self._add_appliance)
        appliance_form.addWidget(self.appliance_name, 1)
        appliance_form.addWidget(QLabel("Isıl güç (kW)"))
        appliance_form.addWidget(self.appliance_power)
        appliance_form.addWidget(self.add_appliance_button)
        layout.addLayout(appliance_form)

        self.appliance_table = QTableWidget(0, 3)
        self.appliance_table.setHorizontalHeaderLabels(["Cihaz", "Isıl güç", "Revizyon"])
        self._configure_table(self.appliance_table)
        layout.addWidget(self.appliance_table, 2)

        calculation_form = QFormLayout()
        self.jurisdiction = QLineEdit()
        self.jurisdiction.setPlaceholderText("İsteğe bağlı; örn. KZ veya TR")
        self.effective_date = QDateEdit()
        self.effective_date.setCalendarPopup(True)
        self.effective_date.setDisplayFormat("yyyy-MM-dd")
        self.effective_date.setDate(date.today())
        calculation_form.addRow("Mevzuat alanı", self.jurisdiction)
        calculation_form.addRow("Geçerlilik tarihi", self.effective_date)
        layout.addLayout(calculation_form)

        actions = QHBoxLayout()
        self.calculate_button = QPushButton("Gaz debisini hesapla")
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.clicked.connect(self._calculate)
        actions.addWidget(self.calculate_button)
        self.status_label = QLabel("Hesaplama için proje seçin.")
        self.status_label.setObjectName("mutedText")
        actions.addWidget(self.status_label, 1)
        layout.addLayout(actions)

        result_title = QLabel("Hesaplama sonuçları")
        result_title.setObjectName("sectionTitle")
        layout.addWidget(result_title)
        self.result_table = QTableWidget(0, 3)
        self.result_table.setHorizontalHeaderLabels(["Sonuç", "Değer", "Birim"])
        self._configure_table(self.result_table)
        layout.addWidget(self.result_table, 2)

        self.refresh()

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

    def refresh(self) -> None:
        previous_id = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for project in self.project_repository.list():
            self.project_combo.addItem(
                f"{project.project_code} — {project.name}",
                str(project.id),
            )
        if previous_id:
            index = self.project_combo.findData(previous_id)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
        self.project_combo.blockSignals(False)
        self._load_selected_project()

    def _selected_project_id(self) -> UUID | None:
        value = self.project_combo.currentData()
        return UUID(str(value)) if value else None

    @staticmethod
    def _gas_appliances(model):
        return tuple(
            item
            for item in model.objects
            if isinstance(item, Equipment)
            and item.equipment_type == "appliance"
            and item.discipline_code == "GAS"
        )

    def _load_selected_project(self, *_args) -> None:
        project_id = self._selected_project_id()
        self.appliance_table.setRowCount(0)
        has_project = project_id is not None
        self.add_appliance_button.setEnabled(has_project)
        self.calculate_button.setEnabled(has_project)
        if not project_id:
            self.status_label.setText("Hesaplama için proje oluşturun veya seçin.")
            return

        try:
            model = self.project_repository.get(project_id)
        except ProjectNotFoundError as exc:
            self.status_label.setText(str(exc))
            return

        appliances = self._gas_appliances(model)
        self.appliance_table.setRowCount(len(appliances))
        for row, appliance in enumerate(appliances):
            power = next(
                (
                    prop.value.quantity
                    for prop in appliance.properties
                    if prop.key == "thermal_input_power"
                    and isinstance(prop.value, QuantityValue)
                ),
                None,
            )
            values = (
                appliance.name,
                f"{power.value} {power.unit_code}" if power else "Eksik",
                str(appliance.revision_id or "—"),
            )
            for column, value in enumerate(values):
                self.appliance_table.setItem(row, column, QTableWidgetItem(value))
        self.status_label.setText(f"{len(appliances)} doğalgaz cihazı kayıtlı.")

    def _add_appliance(self) -> None:
        project_id = self._selected_project_id()
        if project_id is None:
            return
        try:
            name = self.appliance_name.text().strip()
            power = Decimal(self.appliance_power.text().strip())
            model = self.project_repository.get(project_id)
            updated_model = add_gas_appliance(
                model,
                name=name,
                thermal_input_power_kw=power,
                changed_by="local-user",
            )
            self.project_repository.save(updated_model)
        except (InvalidOperation, ValueError, TypeError, ProjectNotFoundError) as exc:
            QMessageBox.warning(self, "Cihaz kaydedilemedi", str(exc))
            return

        self.appliance_name.clear()
        self.appliance_power.clear()
        self.result_table.setRowCount(0)
        self._load_selected_project()

    def _calculate(self) -> None:
        project_id = self._selected_project_id()
        if project_id is None:
            return
        try:
            model = self.project_repository.get(project_id)
            appliances = self._gas_appliances(model)
            if not appliances:
                raise ValueError("Önce projeye en az bir doğalgaz cihazı ekleyin.")

            request = CalculationRequest(
                project_id=project_id,
                method_code="GAS.APPLIANCE_DEMAND",
                method_revision="1.0.0",
                input_object_ids=tuple(item.id for item in appliances),
                parameter_codes=(self.PARAMETER_CODE,),
                effective_date=self.effective_date.date().toPython(),
                jurisdiction_code=self.jurisdiction.text().strip().upper() or None,
                purpose=CalculationPurpose.ENGINEERING,
            )
            execution = self.calculation_runner.run_and_save(
                model,
                request,
                self.project_repository,
            )
        except (
            CalculationPreconditionError,
            CalculationAppendError,
            ProjectNotFoundError,
            UnitValidationError,
            LookupError,
            ValueError,
        ) as exc:
            QMessageBox.warning(
                self,
                "Hesaplama başlatılamadı",
                f"{exc}\n\nGAS.LOWER_HEATING_VALUE parametresinin onaylı ve geçerli bir "
                "revizyonu bulunduğunu kontrol edin.",
            )
            return

        self.result_table.setRowCount(len(execution.results))
        for row, result in enumerate(execution.results):
            if isinstance(result.value, QuantityValue):
                value = str(result.value.quantity.value)
                unit = result.value.quantity.unit_code
            else:
                value = str(result.value)
                unit = "—"
            for column, text in enumerate((result.label, value, unit)):
                self.result_table.setItem(row, column, QTableWidgetItem(text))

        if execution.run.state == CalculationState.COMPLETED:
            self.status_label.setText("Hesaplama tamamlandı ve proje geçmişine kaydedildi.")
        else:
            self.status_label.setText("Hesaplama başarısız; hata kaydı proje geçmişine eklendi.")
            QMessageBox.warning(
                self,
                "Gaz debisi hesaplanamadı",
                execution.error or "Hesap motoru beklenmeyen bir hata döndürdü.",
            )
        self._load_selected_project()
