from mechpro.domain.base import Revision
from mechpro.domain.engineering import LinearElement
from mechpro.domain.project import EngineeringSystem
from mechpro.domain.validation_context import ValidationContext


def validate_engineering_objects(ctx: ValidationContext) -> None:
    model = ctx.model

    for index, obj in enumerate(model.objects):
        path = f"objects[{index}]"
        if obj.project_id != model.project.id:
            ctx.add("wrong_project", "Engineering object must belong to the model project.", path)
        if obj.discipline_code not in ctx.discipline_codes:
            ctx.add(
                "missing_discipline",
                f"Discipline '{obj.discipline_code}' is not registered.",
                path,
            )
        if obj.system_id is not None:
            system = ctx.require(
                obj.system_id,
                EngineeringSystem,
                f"{path}.system_id",
                "Object system",
            )
            if system is not None and system.discipline_code != obj.discipline_code:
                ctx.add(
                    "discipline_system_mismatch",
                    "Object discipline does not match its system discipline.",
                    path,
                )
        if obj.level_id is not None and obj.level_id not in ctx.level_ids:
            ctx.add("missing_level", "Engineering object references an unknown level.", f"{path}.level_id")

        ctx.validate_sources(obj.source_reference_ids, f"{path}.source_reference_ids")
        for geometry_id in obj.geometry_reference_ids:
            if geometry_id not in ctx.geometry_ids:
                ctx.add(
                    "missing_geometry",
                    f"Geometry reference '{geometry_id}' does not exist.",
                    f"{path}.geometry_reference_ids",
                )

        if obj.revision_id is not None:
            revision = ctx.revision_by_id.get(obj.revision_id)
            if revision is None or revision.object_id != obj.id:
                ctx.add(
                    "revision_mismatch",
                    "Object revision must exist and belong to this object.",
                    f"{path}.revision_id",
                )

        connector_codes: set[str] = set()
        for connector_index, connector in enumerate(obj.connectors):
            connector_path = f"{path}.connectors[{connector_index}]"
            if connector.id in ctx.connector_owner:
                ctx.add(
                    "duplicate_connector_id",
                    "Connector ID is used by more than one object.",
                    connector_path,
                )
            else:
                ctx.connector_owner[connector.id] = obj.id
            if connector.code in connector_codes:
                ctx.add(
                    "duplicate_connector_code",
                    f"Connector code '{connector.code}' is duplicated on this object.",
                    connector_path,
                )
            connector_codes.add(connector.code)

        for property_index, prop in enumerate(obj.properties):
            property_path = f"{path}.properties[{property_index}]"
            ctx.validate_sources(prop.source_reference_ids, f"{property_path}.source_reference_ids")
            if (
                prop.standard_reference_id is not None
                and prop.standard_reference_id not in ctx.standard_ids
            ):
                ctx.add(
                    "missing_standard",
                    "Property standard reference does not exist.",
                    f"{property_path}.standard_reference_id",
                )
            if prop.revision_id is not None:
                ctx.require(
                    prop.revision_id,
                    Revision,
                    f"{property_path}.revision_id",
                    "Property revision",
                )
            ctx.validate_property_value(prop.value, f"{property_path}.value")

        if isinstance(obj, LinearElement):
            ctx.validate_unit(obj.length, f"{path}.length", "[length]")
            if (
                obj.material_product_reference_id is not None
                and obj.material_product_reference_id not in ctx.product_by_id
            ):
                ctx.add(
                    "missing_product",
                    "Linear element material product does not exist.",
                    f"{path}.material_product_reference_id",
                )


def validate_engineering_networks(ctx: ValidationContext) -> None:
    model = ctx.model

    for index, network in enumerate(model.networks):
        path = f"networks[{index}]"
        if network.project_id != model.project.id:
            ctx.add("wrong_project", "Network must belong to the model project.", path)
        system = ctx.system_by_id.get(network.system_id)
        if system is None:
            ctx.add("missing_system", "Network references an unknown system.", f"{path}.system_id")
        elif system.project_id != network.project_id:
            ctx.add(
                "wrong_system_project",
                "Network and system belong to different projects.",
                path,
            )
        for member_id in network.member_object_ids:
            member = ctx.object_by_id.get(member_id)
            if member is None:
                ctx.add(
                    "missing_network_member",
                    f"Network member '{member_id}' does not exist.",
                    f"{path}.member_object_ids",
                )
            elif member.system_id != network.system_id:
                ctx.add(
                    "network_member_system_mismatch",
                    "Network member belongs to a different system.",
                    f"{path}.member_object_ids",
                )
        ctx.validate_sources(network.source_reference_ids, f"{path}.source_reference_ids")

        for connection_id in network.connection_ids:
            connection = next(
                (item for item in model.connections if item.id == connection_id),
                None,
            )
            if connection is None:
                ctx.add(
                    "missing_network_connection",
                    f"Connection '{connection_id}' does not exist.",
                    f"{path}.connection_ids",
                )
            elif connection.network_id != network.id:
                ctx.add(
                    "connection_network_mismatch",
                    "Connection references a different network.",
                    f"{path}.connection_ids",
                )

    for index, connection in enumerate(model.connections):
        path = f"connections[{index}]"
        network = ctx.network_by_id.get(connection.network_id)
        if network is None:
            ctx.add("missing_network", "Connection references an unknown network.", f"{path}.network_id")
            continue
        if connection.id not in network.connection_ids:
            ctx.add("connection_not_listed", "Network does not list this connection.", path)

        for side, endpoint in (
            ("from_endpoint", connection.from_endpoint),
            ("to_endpoint", connection.to_endpoint),
        ):
            if endpoint.object_id not in ctx.object_by_id:
                ctx.add(
                    "connection_object_missing",
                    f"{side} references an unknown engineering object.",
                    f"{path}.{side}",
                )
                continue
            if endpoint.object_id not in network.member_object_ids:
                ctx.add(
                    "connection_object_not_member",
                    f"{side} object is not a member of this network.",
                    f"{path}.{side}",
                )
            if ctx.connector_owner.get(endpoint.connector_id) != endpoint.object_id:
                ctx.add(
                    "connection_connector_missing",
                    f"{side} connector does not belong to the referenced object.",
                    f"{path}.{side}",
                )
        ctx.validate_sources(connection.source_reference_ids, f"{path}.source_reference_ids")
