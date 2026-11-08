from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from mechpro.domain.base import (
    Quantity,
    QuantityValue,
    Revision,
    SourceReference,
    StandardReference,
)
from mechpro.domain.calculations import CalculationResult
from mechpro.domain.commercial import PositionProductMapping
from mechpro.domain.engineering import EngineeringObjectRecord, LinearElement
from mechpro.domain.enums import ValidationSeverity
from mechpro.domain.model import EngineeringModel
from mechpro.domain.project import Building, Discipline, EngineeringSystem, Level, Project
from mechpro.domain.units import UnitService, UnitValidationError


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    path: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )

    def raise_for_errors(self) -> None:
        if self.errors:
            details = "; ".join(
                f"{issue.path}: {issue.message}" for issue in self.errors
            )
            raise ModelValidationError(details)


class ModelValidationError(ValueError):
    pass


class ModelValidator:
    """Validates references, graph connectivity, provenance and quantity dimensions."""

    def __init__(self, unit_service: UnitService | None = None) -> None:
        self._units = unit_service or UnitService()

    def validate(self, model: EngineeringModel) -> ValidationReport:
        issues: list[ValidationIssue] = []
        entities: dict[UUID, object] = {}
        entity_paths: dict[UUID, str] = {}

        def register(entity: object, path: str) -> None:
            entity_id = getattr(entity, "id")
            if entity_id in entities:
                issues.append(
                    ValidationIssue(
                        "duplicate_id",
                        f"ID is already used by {entity_paths[entity_id]}.",
                        path,
                    )
                )
                return
            entities[entity_id] = entity
            entity_paths[entity_id] = path

        collections = (
            ("project", (model.project,)),
            ("buildings", model.buildings),
            ("levels", model.levels),
            ("spaces", model.spaces),
            ("disciplines", model.disciplines),
            ("systems", model.systems),
            ("source_references", model.source_references),
            ("geometry_references", model.geometry_references),
            ("standard_references", model.standard_references),
            ("revisions", model.revisions),
            ("approvals", model.approvals),
            ("objects", model.objects),
            ("networks", model.networks),
            ("connections", model.connections),
            ("products", model.products),
            ("positions", model.positions),
            ("position_product_mappings", model.position_product_mappings),
            ("bom_documents", model.bom_documents),
            ("boq_documents", model.boq_documents),
            ("calculation_runs", model.calculation_runs),
            ("calculation_results", model.calculation_results),
        )
        for collection_name, collection in collections:
            for index, entity in enumerate(collection):
                register(entity, f"{collection_name}[{index}]")

        def require(
            reference_id: UUID | None,
            expected_type: type,
            path: str,
            description: str,
        ) -> object | None:
            if reference_id is None:
                return None
            target = entities.get(reference_id)
            if target is None:
                issues.append(
                    ValidationIssue(
                        "missing_reference",
                        f"{description} references unknown ID '{reference_id}'.",
                        path,
                    )
                )
                return None
            if not isinstance(target, expected_type):
                issues.append(
                    ValidationIssue(
                        "wrong_reference_type",
                        f"{description} points to an incompatible record.",
                        path,
                    )
                )
                return None
            return target

        source_ids = {item.id for item in model.source_references}
        geometry_ids = {item.id for item in model.geometry_references}
        standard_ids = {item.id for item in model.standard_references}
        revision_by_id = {item.id: item for item in model.revisions}
        object_by_id = {item.id: item for item in model.objects}
        network_by_id = {item.id: item for item in model.networks}
        system_by_id = {item.id: item for item in model.systems}
        product_by_id = {item.id: item for item in model.products}
        position_by_id = {item.id: item for item in model.positions}
        mapping_by_id = {item.id: item for item in model.position_product_mappings}
        run_by_id = {item.id: item for item in model.calculation_runs}
        level_ids = {item.id for item in model.levels}
        discipline_codes = {item.code for item in model.disciplines}
        connector_owner: dict[UUID, UUID] = {}

        def validate_source_ids(ids: tuple[UUID, ...], path: str) -> None:
            for source_id in ids:
                if source_id not in source_ids:
                    issues.append(
                        ValidationIssue(
                            "missing_source",
                            f"Source reference '{source_id}' does not exist.",
                            path,
                        )
                    )

        def validate_unit(
            quantity: Quantity,
            path: str,
            expected_dimension: str | None = None,
        ) -> None:
            try:
                self._units.validate(quantity, expected_dimension=expected_dimension)
            except UnitValidationError as exc:
                issues.append(ValidationIssue("invalid_unit", str(exc), path))

        for index, building in enumerate(model.buildings):
            require(building.project_id, Project, f"buildings[{index}].project_id", "Building project")
            if building.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "Building must belong to the model project.",
                        f"buildings[{index}]",
                    )
                )

        building_ids = {item.id for item in model.buildings}
        for index, level in enumerate(model.levels):
            if level.building_id not in building_ids:
                issues.append(
                    ValidationIssue(
                        "missing_building",
                        "Level references an unknown building.",
                        f"levels[{index}].building_id",
                    )
                )
            if level.elevation is not None:
                validate_unit(level.elevation, f"levels[{index}].elevation", "[length]")

        for index, space in enumerate(model.spaces):
            if space.level_id not in level_ids:
                issues.append(
                    ValidationIssue(
                        "missing_level",
                        "Space references an unknown level.",
                        f"spaces[{index}].level_id",
                    )
                )
            if space.area is not None:
                validate_unit(space.area, f"spaces[{index}].area", "[length] ** 2")
            if space.volume is not None:
                validate_unit(space.volume, f"spaces[{index}].volume", "[length] ** 3")

        for index, system in enumerate(model.systems):
            if system.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "System must belong to the model project.",
                        f"systems[{index}]",
                    )
                )
            if system.discipline_code not in discipline_codes:
                issues.append(
                    ValidationIssue(
                        "missing_discipline",
                        f"Discipline '{system.discipline_code}' is not registered.",
                        f"systems[{index}].discipline_code",
                    )
                )

        for index, geometry in enumerate(model.geometry_references):
            if geometry.source_reference_id is not None:
                require(
                    geometry.source_reference_id,
                    SourceReference,
                    f"geometry_references[{index}].source_reference_id",
                    "Geometry source",
                )

        for index, standard in enumerate(model.standard_references):
            if standard.source_reference_id is not None:
                require(
                    standard.source_reference_id,
                    SourceReference,
                    f"standard_references[{index}].source_reference_id",
                    "Standard source",
                )

        for index, revision in enumerate(model.revisions):
            if revision.parent_revision_id is not None:
                parent = require(
                    revision.parent_revision_id,
                    Revision,
                    f"revisions[{index}].parent_revision_id",
                    "Parent revision",
                )
                if parent is not None and parent.object_id != revision.object_id:
                    issues.append(
                        ValidationIssue(
                            "revision_parent_mismatch",
                            "Parent revision belongs to a different object.",
                            f"revisions[{index}].parent_revision_id",
                        )
                    )
            if revision.object_id not in entities:
                issues.append(
                    ValidationIssue(
                        "revision_object_missing",
                        "Revision points to an unknown object or record.",
                        f"revisions[{index}].object_id",
                    )
                )

        for index, obj in enumerate(model.objects):
            path = f"objects[{index}]"
            if obj.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "Engineering object must belong to the model project.",
                        path,
                    )
                )
            if obj.discipline_code not in discipline_codes:
                issues.append(
                    ValidationIssue(
                        "missing_discipline",
                        f"Discipline '{obj.discipline_code}' is not registered.",
                        path,
                    )
                )
            if obj.system_id is not None:
                system = require(obj.system_id, EngineeringSystem, f"{path}.system_id", "Object system")
                if system is not None and system.discipline_code != obj.discipline_code:
                    issues.append(
                        ValidationIssue(
                            "discipline_system_mismatch",
                            "Object discipline does not match its system discipline.",
                            path,
                        )
                    )
            if obj.level_id is not None and obj.level_id not in level_ids:
                issues.append(
                    ValidationIssue(
                        "missing_level",
                        "Engineering object references an unknown level.",
                        f"{path}.level_id",
                    )
                )
            validate_source_ids(obj.source_reference_ids, f"{path}.source_reference_ids")
            for geometry_id in obj.geometry_reference_ids:
                if geometry_id not in geometry_ids:
                    issues.append(
                        ValidationIssue(
                            "missing_geometry",
                            f"Geometry reference '{geometry_id}' does not exist.",
                            f"{path}.geometry_reference_ids",
                        )
                    )
            if obj.revision_id is not None:
                revision = revision_by_id.get(obj.revision_id)
                if revision is None or revision.object_id != obj.id:
                    issues.append(
                        ValidationIssue(
                            "revision_mismatch",
                            "Object revision must exist and belong to this object.",
                            f"{path}.revision_id",
                        )
                    )
            connector_codes: set[str] = set()
            for connector_index, connector in enumerate(obj.connectors):
                connector_path = f"{path}.connectors[{connector_index}]"
                if connector.id in connector_owner:
                    issues.append(
                        ValidationIssue(
                            "duplicate_connector_id",
                            "Connector ID is used by more than one object.",
                            connector_path,
                        )
                    )
                else:
                    connector_owner[connector.id] = obj.id
                if connector.code in connector_codes:
                    issues.append(
                        ValidationIssue(
                            "duplicate_connector_code",
                            f"Connector code '{connector.code}' is duplicated on this object.",
                            connector_path,
                        )
                    )
                connector_codes.add(connector.code)
            for property_index, prop in enumerate(obj.properties):
                property_path = f"{path}.properties[{property_index}]"
                validate_source_ids(prop.source_reference_ids, f"{property_path}.source_reference_ids")
                if prop.standard_reference_id is not None and prop.standard_reference_id not in standard_ids:
                    issues.append(
                        ValidationIssue(
                            "missing_standard",
                            "Property standard reference does not exist.",
                            f"{property_path}.standard_reference_id",
                        )
                    )
                if prop.revision_id is not None:
                    require(prop.revision_id, Revision, f"{property_path}.revision_id", "Property revision")
                if isinstance(prop.value, QuantityValue):
                    validate_unit(prop.value.quantity, f"{property_path}.value")
                elif getattr(prop.value, "kind", None) == "reference":
                    if prop.value.target_id not in entities:
                        issues.append(
                            ValidationIssue(
                                "property_reference_missing",
                                "Property references an unknown record.",
                                f"{property_path}.value.target_id",
                            )
                        )
            if isinstance(obj, LinearElement):
                validate_unit(obj.length, f"{path}.length", "[length]")
                if (
                    obj.material_product_reference_id is not None
                    and obj.material_product_reference_id not in product_by_id
                ):
                    issues.append(
                        ValidationIssue(
                            "missing_product",
                            "Linear element material product does not exist.",
                            f"{path}.material_product_reference_id",
                        )
                    )

        for index, network in enumerate(model.networks):
            path = f"networks[{index}]"
            if network.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "Network must belong to the model project.",
                        path,
                    )
                )
            system = system_by_id.get(network.system_id)
            if system is None:
                issues.append(
                    ValidationIssue(
                        "missing_system",
                        "Network references an unknown system.",
                        f"{path}.system_id",
                    )
                )
            elif system.project_id != network.project_id:
                issues.append(
                    ValidationIssue(
                        "wrong_system_project",
                        "Network and system belong to different projects.",
                        path,
                    )
                )
            for member_id in network.member_object_ids:
                member = object_by_id.get(member_id)
                if member is None:
                    issues.append(
                        ValidationIssue(
                            "missing_network_member",
                            f"Network member '{member_id}' does not exist.",
                            f"{path}.member_object_ids",
                        )
                    )
                elif member.system_id != network.system_id:
                    issues.append(
                        ValidationIssue(
                            "network_member_system_mismatch",
                            "Network member belongs to a different system.",
                            f"{path}.member_object_ids",
                        )
                    )
            validate_source_ids(network.source_reference_ids, f"{path}.source_reference_ids")
            for connection_id in network.connection_ids:
                connection = next((item for item in model.connections if item.id == connection_id), None)
                if connection is None:
                    issues.append(
                        ValidationIssue(
                            "missing_network_connection",
                            f"Connection '{connection_id}' does not exist.",
                            f"{path}.connection_ids",
                        )
                    )
                elif connection.network_id != network.id:
                    issues.append(
                        ValidationIssue(
                            "connection_network_mismatch",
                            "Connection references a different network.",
                            f"{path}.connection_ids",
                        )
                    )

        for index, connection in enumerate(model.connections):
            path = f"connections[{index}]"
            network = network_by_id.get(connection.network_id)
            if network is None:
                issues.append(
                    ValidationIssue(
                        "missing_network",
                        "Connection references an unknown network.",
                        f"{path}.network_id",
                    )
                )
                continue
            if connection.id not in network.connection_ids:
                issues.append(
                    ValidationIssue(
                        "connection_not_listed",
                        "Network does not list this connection.",
                        path,
                    )
                )
            for side, endpoint in (
                ("from_endpoint", connection.from_endpoint),
                ("to_endpoint", connection.to_endpoint),
            ):
                if endpoint.object_id not in object_by_id:
                    issues.append(
                        ValidationIssue(
                            "connection_object_missing",
                            f"{side} references an unknown engineering object.",
                            f"{path}.{side}",
                        )
                    )
                    continue
                if endpoint.object_id not in network.member_object_ids:
                    issues.append(
                        ValidationIssue(
                            "connection_object_not_member",
                            f"{side} object is not a member of this network.",
                            f"{path}.{side}",
                        )
                    )
                if connector_owner.get(endpoint.connector_id) != endpoint.object_id:
                    issues.append(
                        ValidationIssue(
                            "connection_connector_missing",
                            f"{side} connector does not belong to the referenced object.",
                            f"{path}.{side}",
                        )
                    )
            validate_source_ids(connection.source_reference_ids, f"{path}.source_reference_ids")

        for index, product in enumerate(model.products):
            validate_source_ids(product.source_reference_ids, f"products[{index}].source_reference_ids")
            self._validate_unit_code(product.unit_code, f"products[{index}].unit_code", issues)

        for index, position in enumerate(model.positions):
            validate_source_ids(position.source_reference_ids, f"positions[{index}].source_reference_ids")
            self._validate_unit_code(position.unit_code, f"positions[{index}].unit_code", issues)

        for index, mapping in enumerate(model.position_product_mappings):
            if mapping.position_reference_id not in position_by_id:
                issues.append(
                    ValidationIssue(
                        "missing_position",
                        "Mapping references an unknown BOQ position.",
                        f"position_product_mappings[{index}]",
                    )
                )
            if mapping.product_reference_id not in product_by_id:
                issues.append(
                    ValidationIssue(
                        "missing_product",
                        "Mapping references an unknown physical product.",
                        f"position_product_mappings[{index}]",
                    )
                )
            validate_source_ids(
                mapping.source_reference_ids,
                f"position_product_mappings[{index}].source_reference_ids",
            )

        for index, document in enumerate(model.bom_documents):
            if document.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "BOM document belongs to a different project.",
                        f"bom_documents[{index}]",
                    )
                )
            if document.model_revision_id is not None:
                revision = revision_by_id.get(document.model_revision_id)
                if revision is None or revision.object_id != model.project.id:
                    issues.append(
                        ValidationIssue(
                            "bom_revision_mismatch",
                            "BOM must reference a revision of its project model.",
                            f"bom_documents[{index}].model_revision_id",
                        )
                    )
            for item_index, item in enumerate(document.items):
                path = f"bom_documents[{index}].items[{item_index}]"
                product = product_by_id.get(item.product_reference_id)
                if product is None:
                    issues.append(ValidationIssue("missing_product", "BOM item product does not exist.", path))
                else:
                    validate_unit(item.quantity, f"{path}.quantity")
                    if not self._units.are_compatible(item.quantity.unit_code, product.unit_code):
                        issues.append(
                            ValidationIssue(
                                "bom_unit_mismatch",
                                f"BOM quantity unit '{item.quantity.unit_code}' is incompatible with product unit '{product.unit_code}'.",
                                path,
                            )
                        )
                self._validate_object_sources(item.source_object_ids, object_by_id, path, issues)

        for index, document in enumerate(model.boq_documents):
            if document.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "BOQ document belongs to a different project.",
                        f"boq_documents[{index}]",
                    )
                )
            if document.model_revision_id is not None:
                revision = revision_by_id.get(document.model_revision_id)
                if revision is None or revision.object_id != model.project.id:
                    issues.append(
                        ValidationIssue(
                            "boq_revision_mismatch",
                            "BOQ must reference a revision of its project model.",
                            f"boq_documents[{index}].model_revision_id",
                        )
                    )
            for item_index, item in enumerate(document.items):
                path = f"boq_documents[{index}].items[{item_index}]"
                position = position_by_id.get(item.position_reference_id)
                if position is None:
                    issues.append(ValidationIssue("missing_position", "BOQ item position does not exist.", path))
                else:
                    validate_unit(item.quantity, f"{path}.quantity")
                    if not self._units.are_compatible(item.quantity.unit_code, position.unit_code):
                        issues.append(
                            ValidationIssue(
                                "boq_unit_mismatch",
                                f"BOQ quantity unit '{item.quantity.unit_code}' is incompatible with position unit '{position.unit_code}'.",
                                path,
                            )
                        )
                mapping = mapping_by_id.get(item.mapping_id)
                if mapping is None:
                    issues.append(
                        ValidationIssue(
                            "missing_mapping",
                            "BOQ item mapping does not exist.",
                            f"{path}.mapping_id",
                        )
                    )
                elif mapping.position_reference_id != item.position_reference_id:
                    issues.append(
                        ValidationIssue(
                            "mapping_position_mismatch",
                            "BOQ item and mapping refer to different positions.",
                            path,
                        )
                    )
                elif mapping.measurement_rule_code != item.measurement_rule_code:
                    issues.append(
                        ValidationIssue(
                            "measurement_rule_mismatch",
                            "BOQ item measurement rule differs from its mapping rule.",
                            path,
                        )
                    )
                elif not mapping.enabled:
                    issues.append(
                        ValidationIssue(
                            "inactive_mapping",
                            "BOQ item uses a disabled position-product mapping.",
                            path,
                            ValidationSeverity.WARNING,
                        )
                    )
                self._validate_object_sources(item.source_object_ids, object_by_id, path, issues)

        for index, run in enumerate(model.calculation_runs):
            path = f"calculation_runs[{index}]"
            if run.project_id != model.project.id:
                issues.append(
                    ValidationIssue(
                        "wrong_project",
                        "Calculation run belongs to a different project.",
                        path,
                    )
                )
            for standard_id in run.standard_reference_ids:
                if standard_id not in standard_ids:
                    issues.append(
                        ValidationIssue(
                            "missing_standard",
                            f"Calculation standard '{standard_id}' does not exist.",
                            f"{path}.standard_reference_ids",
                        )
                    )
            for input_index, snapshot in enumerate(run.input_snapshots):
                input_path = f"{path}.input_snapshots[{input_index}]"
                if snapshot.engineering_object_id not in object_by_id:
                    issues.append(
                        ValidationIssue(
                            "calculation_object_missing",
                            "Calculation input references an unknown engineering object.",
                            input_path,
                        )
                    )
                revision = revision_by_id.get(snapshot.object_revision_id)
                if revision is None or revision.object_id != snapshot.engineering_object_id:
                    issues.append(
                        ValidationIssue(
                            "calculation_revision_missing",
                            "Calculation input must reference a revision of its source object.",
                            input_path,
                        )
                    )
                validate_source_ids(snapshot.source_reference_ids, f"{input_path}.source_reference_ids")
                for prop_index, prop in enumerate(snapshot.property_snapshots):
                    validate_source_ids(
                        prop.source_reference_ids,
                        f"{input_path}.property_snapshots[{prop_index}].source_reference_ids",
                    )
                    if isinstance(prop.value, QuantityValue):
                        validate_unit(
                            prop.value.quantity,
                            f"{input_path}.property_snapshots[{prop_index}].value",
                        )
                for parameter_index, parameter in enumerate(snapshot.parameter_snapshots):
                    validate_source_ids(
                        parameter.source_reference_ids,
                        f"{input_path}.parameter_snapshots[{parameter_index}].source_reference_ids",
                    )
                    if isinstance(parameter.value, QuantityValue):
                        validate_unit(
                            parameter.value.quantity,
                            f"{input_path}.parameter_snapshots[{parameter_index}].value",
                        )

        for index, result in enumerate(model.calculation_results):
            path = f"calculation_results[{index}]"
            run = run_by_id.get(result.calculation_run_id)
            if run is None:
                issues.append(
                    ValidationIssue(
                        "calculation_run_missing",
                        "Calculation result references an unknown run.",
                        f"{path}.calculation_run_id",
                    )
                )
            for object_id in result.source_object_ids:
                if object_id not in object_by_id:
                    issues.append(
                        ValidationIssue(
                            "result_source_missing",
                            f"Result source object '{object_id}' does not exist.",
                            f"{path}.source_object_ids",
                        )
                    )
            if isinstance(result.value, QuantityValue):
                validate_unit(result.value.quantity, f"{path}.value")
            for standard_id in result.standard_reference_ids:
                if standard_id not in standard_ids:
                    issues.append(
                        ValidationIssue(
                            "missing_standard",
                            f"Result standard '{standard_id}' does not exist.",
                            f"{path}.standard_reference_ids",
                        )
                    )

        for index, approval in enumerate(model.approvals):
            if approval.revision_id not in revision_by_id:
                issues.append(
                    ValidationIssue(
                        "approval_revision_missing",
                        "Approval points to an unknown revision.",
                        f"approvals[{index}].revision_id",
                    )
                )

        return ValidationReport(tuple(issues))

    def _validate_unit_code(
        self,
        unit_code: str,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        try:
            self._units.validate(Quantity(value=Decimal("1"), unit_code=unit_code))
        except UnitValidationError as exc:
            issues.append(ValidationIssue("invalid_unit", str(exc), path))

    @staticmethod
    def _validate_object_sources(
        source_ids: tuple[UUID, ...],
        object_by_id: dict[UUID, EngineeringObjectRecord],
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        for object_id in source_ids:
            if object_id not in object_by_id:
                issues.append(
                    ValidationIssue(
                        "missing_source_object",
                        f"Source object '{object_id}' does not exist.",
                        path,
                    )
                )
