from mechprox.domain.engineering import Equipment, LinearElement
from mechprox.domain.enums import ValidationSeverity
from mechprox.domain.validation_context import ValidationContext


def _assigned_product_id(obj: object):
    if isinstance(obj, LinearElement):
        return obj.material_product_reference_id
    if isinstance(obj, Equipment):
        return obj.product_reference_id
    return None


def validate_commercial_records(ctx: ValidationContext) -> None:
    model = ctx.model

    for index, product in enumerate(model.products):
        ctx.validate_sources(
            product.source_reference_ids,
            f"products[{index}].source_reference_ids",
        )
        ctx.validate_unit_code(product.unit_code, f"products[{index}].unit_code")

    for index, position in enumerate(model.positions):
        ctx.validate_sources(
            position.source_reference_ids,
            f"positions[{index}].source_reference_ids",
        )
        ctx.validate_unit_code(position.unit_code, f"positions[{index}].unit_code")

    for index, mapping in enumerate(model.position_product_mappings):
        path = f"position_product_mappings[{index}]"
        if mapping.position_reference_id not in ctx.position_by_id:
            ctx.add("missing_position", "Mapping references an unknown BOQ position.", path)
        if mapping.product_reference_id not in ctx.product_by_id:
            ctx.add("missing_product", "Mapping references an unknown physical product.", path)
        ctx.validate_sources(mapping.source_reference_ids, f"{path}.source_reference_ids")

    for index, document in enumerate(model.bom_documents):
        path = f"bom_documents[{index}]"
        if document.project_id != model.project.id:
            ctx.add("wrong_project", "BOM document belongs to a different project.", path)
        if document.model_revision_id is not None:
            revision = ctx.revision_by_id.get(document.model_revision_id)
            if revision is None or revision.object_id != model.project.id:
                ctx.add(
                    "bom_revision_mismatch",
                    "BOM must reference a revision of its project model.",
                    f"{path}.model_revision_id",
                )
        for item_index, item in enumerate(document.items):
            item_path = f"{path}.items[{item_index}]"
            product = ctx.product_by_id.get(item.product_reference_id)
            if product is None:
                ctx.add("missing_product", "BOM item product does not exist.", item_path)
            else:
                ctx.validate_unit(item.quantity, f"{item_path}.quantity")
                if not ctx.units.are_compatible(item.quantity.unit_code, product.unit_code):
                    ctx.add(
                        "bom_unit_mismatch",
                        f"BOM quantity unit '{item.quantity.unit_code}' is incompatible with product unit '{product.unit_code}'.",
                        item_path,
                    )
            ctx.validate_object_sources(item.source_object_ids, item_path)
            for source_id in item.source_object_ids:
                source_object = ctx.object_by_id.get(source_id)
                assigned_product_id = (
                    _assigned_product_id(source_object)
                    if source_object is not None
                    else None
                )
                if assigned_product_id is not None and assigned_product_id != item.product_reference_id:
                    ctx.add(
                        "bom_source_product_mismatch",
                        "BOM product does not match the product assigned to a source object.",
                        item_path,
                    )

    for index, document in enumerate(model.boq_documents):
        path = f"boq_documents[{index}]"
        if document.project_id != model.project.id:
            ctx.add("wrong_project", "BOQ document belongs to a different project.", path)
        if document.model_revision_id is not None:
            revision = ctx.revision_by_id.get(document.model_revision_id)
            if revision is None or revision.object_id != model.project.id:
                ctx.add(
                    "boq_revision_mismatch",
                    "BOQ must reference a revision of its project model.",
                    f"{path}.model_revision_id",
                )
        for item_index, item in enumerate(document.items):
            item_path = f"{path}.items[{item_index}]"
            position = ctx.position_by_id.get(item.position_reference_id)
            if position is None:
                ctx.add("missing_position", "BOQ item position does not exist.", item_path)
            else:
                ctx.validate_unit(item.quantity, f"{item_path}.quantity")
                if not ctx.units.are_compatible(item.quantity.unit_code, position.unit_code):
                    ctx.add(
                        "boq_unit_mismatch",
                        f"BOQ quantity unit '{item.quantity.unit_code}' is incompatible with position unit '{position.unit_code}'.",
                        item_path,
                    )

            mapping = ctx.mapping_by_id.get(item.mapping_id)
            if mapping is None:
                ctx.add("missing_mapping", "BOQ item mapping does not exist.", f"{item_path}.mapping_id")
            else:
                if mapping.position_reference_id != item.position_reference_id:
                    ctx.add(
                        "mapping_position_mismatch",
                        "BOQ item and mapping refer to different positions.",
                        item_path,
                    )
                if mapping.measurement_rule_code != item.measurement_rule_code:
                    ctx.add(
                        "measurement_rule_mismatch",
                        "BOQ item measurement rule differs from its mapping rule.",
                        item_path,
                    )
                if mapping.mapping_version != item.measurement_rule_version:
                    ctx.add(
                        "measurement_rule_version_mismatch",
                        "BOQ item measurement-rule version differs from its mapping version.",
                        item_path,
                    )
                if not mapping.enabled:
                    ctx.add(
                        "inactive_mapping",
                        "BOQ item uses a disabled position-product mapping.",
                        item_path,
                        severity=ValidationSeverity.WARNING,
                    )
                for source_id in item.source_object_ids:
                    source_object = ctx.object_by_id.get(source_id)
                    assigned_product_id = (
                        _assigned_product_id(source_object)
                        if source_object is not None
                        else None
                    )
                    if (
                        assigned_product_id is not None
                        and assigned_product_id != mapping.product_reference_id
                    ):
                        ctx.add(
                            "boq_source_product_mismatch",
                            "BOQ mapping product differs from the product assigned to a source object.",
                            item_path,
                        )
            ctx.validate_object_sources(item.source_object_ids, item_path)
