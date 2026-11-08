from decimal import Decimal
from uuid import UUID

from mechprox.domain.base import (
    EngineeringProperty,
    GeometryReference,
    Quantity,
    QuantityValue,
    Revision,
    ScalarValue,
    SourceReference,
)
from mechprox.domain.calculations import (
    CalculationInputSnapshot,
    CalculationResult,
    CalculationRun,
    ParameterSnapshot,
)
from mechprox.domain.commercial import (
    BOMDocument,
    BOMItem,
    BOQDocument,
    BOQItem,
    PositionProductMapping,
    PositionReference,
    ProductReference,
)
from mechprox.domain.engineering import (
    Connector,
    ConnectorEndpoint,
    Equipment,
    LinearElement,
)
from mechprox.domain.enums import (
    CalculationPurpose,
    CalculationState,
    ConnectionDirection,
    ConnectionKind,
    ConnectorDirection,
    ConnectorDomain,
    GeometryFormat,
    InformationOrigin,
    RevisionState,
    SourceKind,
)
from mechprox.domain.model import EngineeringModel
from mechprox.domain.network import Connection, Network
from mechprox.domain.project import (
    Building,
    Discipline,
    EngineeringSystem,
    Level,
    Project,
    Space,
)


def _id(value: str) -> UUID:
    return UUID(value)


def create_natural_gas_reference_model() -> EngineeringModel:
    """Synthetic topology example. It contains no engineering design coefficients."""

    project_id = _id("10000000-0000-4000-8000-000000000001")
    building_id = _id("10000000-0000-4000-8000-000000000002")
    level_id = _id("10000000-0000-4000-8000-000000000003")
    discipline_id = _id("10000000-0000-4000-8000-000000000004")
    system_id = _id("10000000-0000-4000-8000-000000000005")
    space_a_id = _id("10000000-0000-4000-8000-000000000006")
    space_b_id = _id("10000000-0000-4000-8000-000000000007")
    network_id = _id("a0000000-0000-4000-8000-000000000001")
    source_ids = [
        _id("20000000-0000-4000-8000-000000000001"),
        _id("20000000-0000-4000-8000-000000000002"),
        _id("20000000-0000-4000-8000-000000000003"),
        _id("20000000-0000-4000-8000-000000000004"),
    ]
    geometry_ids = [
        _id("30000000-0000-4000-8000-000000000001"),
        _id("30000000-0000-4000-8000-000000000002"),
        _id("30000000-0000-4000-8000-000000000003"),
    ]
    source_object_id = _id("40000000-0000-4000-8000-000000000001")
    pipe_ids = [
        _id("40000000-0000-4000-8000-000000000002"),
        _id("40000000-0000-4000-8000-000000000003"),
        _id("40000000-0000-4000-8000-000000000004"),
    ]
    appliance_id = _id("40000000-0000-4000-8000-000000000005")
    source_connector = _id("50000000-0000-4000-8000-000000000001")
    pipe_connectors = [
        (_id("50000000-0000-4000-8000-000000000002"), _id("50000000-0000-4000-8000-000000000003")),
        (_id("50000000-0000-4000-8000-000000000004"), _id("50000000-0000-4000-8000-000000000005")),
        (_id("50000000-0000-4000-8000-000000000006"), _id("50000000-0000-4000-8000-000000000007")),
    ]
    appliance_connector = _id("50000000-0000-4000-8000-000000000008")
    connection_ids = [
        _id("60000000-0000-4000-8000-000000000001"),
        _id("60000000-0000-4000-8000-000000000002"),
        _id("60000000-0000-4000-8000-000000000003"),
        _id("60000000-0000-4000-8000-000000000004"),
    ]
    pipe_product_id = _id("70000000-0000-4000-8000-000000000001")
    pipe_position_id = _id("70000000-0000-4000-8000-000000000002")
    mapping_id = _id("70000000-0000-4000-8000-000000000003")
    run_id = _id("80000000-0000-4000-8000-000000000001")
    result_id = _id("80000000-0000-4000-8000-000000000002")
    revision_ids = [
        _id("90000000-0000-4000-8000-000000000001"),
        _id("90000000-0000-4000-8000-000000000002"),
        _id("90000000-0000-4000-8000-000000000003"),
        _id("90000000-0000-4000-8000-000000000004"),
        _id("90000000-0000-4000-8000-000000000005"),
    ]
    object_ids = [source_object_id, *pipe_ids, appliance_id]
    revisions = tuple(
        Revision(
            id=revision_ids[index],
            object_id=object_id,
            revision_code="A",
            state=RevisionState.DRAFT,
            changed_by="synthetic-example",
            change_summary="Initial reference model record.",
        )
        for index, object_id in enumerate(object_ids)
    )

    source = Equipment(
        id=source_object_id,
        project_id=project_id,
        name="Synthetic gas supply source",
        category_code="gas_supply_source",
        discipline_code="GAS",
        system_id=system_id,
        equipment_type="supply_source",
        information_origin=InformationOrigin.USER_INPUT,
        source_reference_ids=(source_ids[0],),
        revision_id=revision_ids[0],
        connectors=(
            Connector(
                id=source_connector,
                code="outlet",
                domain=ConnectorDomain.FLUID,
                direction=ConnectorDirection.OUTLET,
                nominal_size="DN-DEMO",
            ),
        ),
    )

    pipe_lengths = (Decimal("6.0"), Decimal("4.0"), Decimal("3.0"))
    pipes = tuple(
        LinearElement(
            id=pipe_ids[index],
            project_id=project_id,
            name=f"Synthetic gas pipe segment {index + 1}",
            category_code="pipe",
            discipline_code="GAS",
            system_id=system_id,
            level_id=level_id,
            element_type="pipe_segment",
            length=Quantity(value=pipe_lengths[index], unit_code="meter"),
            nominal_size="DN-DEMO",
            material_product_reference_id=pipe_product_id,
            information_origin=InformationOrigin.DRAWING_IMPORT,
            source_reference_ids=(source_ids[index + 1],),
            geometry_reference_ids=(geometry_ids[index],),
            revision_id=revision_ids[index + 1],
            connectors=(
                Connector(
                    id=pipe_connectors[index][0],
                    code="inlet",
                    domain=ConnectorDomain.FLUID,
                    direction=ConnectorDirection.INLET,
                    nominal_size="DN-DEMO",
                ),
                Connector(
                    id=pipe_connectors[index][1],
                    code="outlet",
                    domain=ConnectorDomain.FLUID,
                    direction=ConnectorDirection.OUTLET,
                    nominal_size="DN-DEMO",
                ),
            ),
            properties=(
                EngineeringProperty(
                    key="nominal_size_label",
                    value=ScalarValue(value="DN-DEMO"),
                    origin=InformationOrigin.DRAWING_IMPORT,
                    source_reference_ids=(source_ids[index + 1],),
                ),
                EngineeringProperty(
                    key="centerline_length",
                    value=QuantityValue(
                        quantity=Quantity(value=pipe_lengths[index], unit_code="meter")
                    ),
                    origin=InformationOrigin.DRAWING_IMPORT,
                    source_reference_ids=(source_ids[index + 1],),
                ),
            ),
        )
        for index in range(3)
    )

    appliance = Equipment(
        id=appliance_id,
        project_id=project_id,
        name="Synthetic gas appliance",
        category_code="gas_appliance",
        discipline_code="GAS",
        system_id=system_id,
        level_id=level_id,
        equipment_type="appliance",
        information_origin=InformationOrigin.USER_INPUT,
        source_reference_ids=(source_ids[0],),
        revision_id=revision_ids[4],
        connectors=(
            Connector(
                id=appliance_connector,
                code="gas_inlet",
                domain=ConnectorDomain.FLUID,
                direction=ConnectorDirection.INLET,
                nominal_size="DN-DEMO",
            ),
        ),
    )

    endpoint_data = [
        (source_object_id, source_connector, pipe_ids[0], pipe_connectors[0][0]),
        (pipe_ids[0], pipe_connectors[0][1], pipe_ids[1], pipe_connectors[1][0]),
        (pipe_ids[1], pipe_connectors[1][1], pipe_ids[2], pipe_connectors[2][0]),
        (pipe_ids[2], pipe_connectors[2][1], appliance_id, appliance_connector),
    ]
    connections = tuple(
        Connection(
            id=connection_ids[index],
            network_id=network_id,
            from_endpoint=ConnectorEndpoint(
                object_id=left_object,
                connector_id=left_connector,
            ),
            to_endpoint=ConnectorEndpoint(
                object_id=right_object,
                connector_id=right_connector,
            ),
            connection_kind=ConnectionKind.PHYSICAL,
            direction=ConnectionDirection.A_TO_B,
            origin=InformationOrigin.DRAWING_IMPORT,
            source_reference_ids=(source_ids[min(index + 1, 3)],),
        )
        for index, (left_object, left_connector, right_object, right_connector) in enumerate(endpoint_data)
    )

    pipe_product = ProductReference(
        id=pipe_product_id,
        catalogue_code="SYNTHETIC-DEMO",
        product_code="PIPE-DEMO",
        name="Synthetic pipe material",
        category_code="pipe",
        unit_code="meter",
        manufacturer="Example only",
        catalogue_revision="demo-1",
        source_reference_ids=(source_ids[0],),
        origin=InformationOrigin.USER_INPUT,
    )
    pipe_position = PositionReference(
        id=pipe_position_id,
        catalogue_code="SYNTHETIC-DEMO",
        position_code="DEMO-POS-PIPE",
        name="Synthetic pipe installation position",
        unit_code="meter",
        catalogue_revision="demo-1",
        source_reference_ids=(source_ids[0],),
    )
    mapping = PositionProductMapping(
        id=mapping_id,
        position_reference_id=pipe_position_id,
        product_reference_id=pipe_product_id,
        mapping_code="DEMO-PIPE-MAPPING",
        mapping_version="1",
        measurement_rule_code="LINEAR_CENTERLINE_LENGTH",
        source_reference_ids=(source_ids[0],),
    )

    total_pipe_length = sum(pipe_lengths, Decimal(0))
    bom = BOMDocument(
        project_id=project_id,
        title="Synthetic material takeoff",
        items=(
            BOMItem(
                product_reference_id=pipe_product_id,
                quantity=Quantity(value=total_pipe_length, unit_code="meter"),
                source_object_ids=tuple(pipe_ids),
                note="Synthetic example total; not a procurement instruction.",
            ),
        ),
    )
    boq = BOQDocument(
        project_id=project_id,
        title="Synthetic BOQ measurement",
        items=(
            BOQItem(
                position_reference_id=pipe_position_id,
                quantity=Quantity(value=total_pipe_length, unit_code="meter"),
                source_object_ids=tuple(pipe_ids),
                mapping_id=mapping_id,
                measurement_rule_code="LINEAR_CENTERLINE_LENGTH",
                measurement_rule_version="1",
                measurement_note="Illustrative mapping only; no public poz is implied.",
            ),
        ),
    )

    input_snapshot = CalculationInputSnapshot(
        engineering_object_id=pipe_ids[0],
        object_revision_id=revision_ids[1],
        property_snapshots=(pipes[0].properties[0], pipes[0].properties[1]),
        source_reference_ids=(source_ids[1],),
        parameter_snapshots=(
            ParameterSnapshot(
                parameter_code="DEMO.DATASET_REVISION",
                value=ScalarValue(value="demo-1"),
                parameter_revision="demo-1",
                source_reference_ids=(source_ids[0],),
            ),
        ),
        snapshot_hash="synthetic-snapshot-hash-not-for-design",
    )
    calculation_run = CalculationRun(
        id=run_id,
        project_id=project_id,
        method_code="DEMO.TRACEABILITY",
        method_revision="demo-1",
        engine_name="reference-only",
        engine_version="not-an-engine",
        purpose=CalculationPurpose.DEMONSTRATION,
        state=CalculationState.COMPLETED,
        input_snapshots=(input_snapshot,),
        input_hash="synthetic-input-hash-not-for-design",
        output_hash="synthetic-output-hash-not-for-design",
    )
    calculation_result = CalculationResult(
        id=result_id,
        calculation_run_id=run_id,
        result_code="traceability_status",
        label="Traceability demonstration only",
        value=ScalarValue(
            value="No engineering algorithm was executed; this is not a design result."
        ),
        source_object_ids=(pipe_ids[0],),
    )

    return EngineeringModel(
        project=Project(
            id=project_id,
            project_code="SYNTHETIC-GAS-001",
            name="Synthetic natural gas network reference model",
            description=(
                "Data model demonstration only. All geometry, dimensions and "
                "commercial entries are synthetic and not suitable for design."
            ),
            client_name="Example only",
        ),
        buildings=(
            Building(
                id=building_id,
                project_id=project_id,
                building_code="BLD-A",
                name="Synthetic building",
            ),
        ),
        levels=(
            Level(
                id=level_id,
                building_id=building_id,
                level_code="L00",
                name="Ground level",
                elevation=Quantity(value=Decimal(0), unit_code="meter"),
            ),
        ),
        spaces=(
            Space(
                id=space_a_id,
                level_id=level_id,
                space_code="S-001",
                name="Utility room",
                area=Quantity(value=Decimal(12), unit_code="meter ** 2"),
            ),
            Space(
                id=space_b_id,
                level_id=level_id,
                space_code="S-002",
                name="Appliance room",
                area=Quantity(value=Decimal(8), unit_code="meter ** 2"),
            ),
        ),
        disciplines=(
            Discipline(id=discipline_id, code="GAS", name="Natural gas"),
        ),
        systems=(
            EngineeringSystem(
                id=system_id,
                project_id=project_id,
                discipline_code="GAS",
                system_code="NG-DEMO",
                name="Synthetic natural gas system",
                system_family="fuel_gas",
            ),
        ),
        source_references=tuple(
            SourceReference(
                id=source_ids[index],
                source_kind=SourceKind.DWG if index else SourceKind.MANUAL,
                uri="project://synthetic/drawings/gas-layout.dwg",
                document_name="gas-layout.dwg",
                document_revision="demo-1",
                external_entity_id=f"DEMO-{index}",
                entity_handle=f"DEMO{index:03d}" if index else None,
                origin=(
                    InformationOrigin.DRAWING_IMPORT
                    if index
                    else InformationOrigin.USER_INPUT
                ),
            )
            for index in range(4)
        ),
        geometry_references=tuple(
            GeometryReference(
                id=geometry_ids[index],
                format=GeometryFormat.DWG,
                file_uri="project://synthetic/drawings/gas-layout.dwg",
                geometry_type="line",
                external_entity_id=f"DEMO{index + 1:03d}",
                coordinate_system="local-demo",
                source_reference_id=source_ids[index + 1],
                geometry_hash=f"synthetic-geometry-DEMO{index + 1:03d}",
            )
            for index in range(3)
        ),
        revisions=revisions,
        objects=(source, *pipes, appliance),
        networks=(
            Network(
                id=network_id,
                project_id=project_id,
                system_id=system_id,
                network_code="NG-NET-DEMO",
                name="Synthetic gas network",
                network_type="branched_pipe_network",
                member_object_ids=tuple(object_ids),
                connection_ids=tuple(connection_ids),
                source_reference_ids=(source_ids[0],),
            ),
        ),
        connections=connections,
        products=(pipe_product,),
        positions=(pipe_position,),
        position_product_mappings=(mapping,),
        bom_documents=(bom,),
        boq_documents=(boq,),
        calculation_runs=(calculation_run,),
        calculation_results=(calculation_result,),
    )
