from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from mechprox.domain.base import Quantity
from mechprox.domain.commercial import (
    BOMDocument, BOMItem, BOQDocument, BOQItem, PositionProductMapping,
    PositionReference, ProductReference,
)
from mechprox.domain.engineering import EngineeringObjectRecord, Equipment, LinearElement
from mechprox.domain.model import EngineeringModel
from mechprox.domain.units import UnitService, UnitValidationError
from mechprox.domain.validation import ModelValidator


@dataclass(frozen=True, slots=True)
class TakeoffResult:
    model: EngineeringModel
    bom: BOMDocument
    boq: BOQDocument
    warnings: tuple[str, ...]


def _assigned_product(obj: EngineeringObjectRecord):
    if isinstance(obj, LinearElement):
        return obj.material_product_reference_id
    if isinstance(obj, Equipment):
        return obj.product_reference_id
    return None


def _object_quantity(obj: EngineeringObjectRecord, product: ProductReference) -> Quantity | None:
    if isinstance(obj, LinearElement):
        return obj.length
    if isinstance(obj, Equipment):
        return Quantity(value=Decimal(1), unit_code="piece")
    return None


def _convert(units: UnitService, quantity: Quantity, target_unit: str) -> Quantity:
    return units.convert(quantity, target_unit)


def generate_takeoff(
    model: EngineeringModel,
    *,
    title: str = "Project takeoff",
    unit_service: UnitService | None = None,
) -> TakeoffResult:
    """Create deterministic BOM/BOQ documents from explicitly product-assigned model objects."""
    units = unit_service or UnitService()
    products = {item.id: item for item in model.products}
    positions = {item.id: item for item in model.positions}
    mappings = {item.id: item for item in model.position_product_mappings}
    warnings: list[str] = []

    bom_groups: dict[object, dict] = {}
    boq_groups: dict[object, dict] = {}

    for obj in model.objects:
        product_id = _assigned_product(obj)
        if product_id is None:
            continue
        product = products.get(product_id)
        if product is None:
            warnings.append(f"{obj.name}: product reference is missing; omitted from BOM.")
            continue
        raw_quantity = _object_quantity(obj, product)
        if raw_quantity is None:
            warnings.append(f"{obj.name}: object type has no supported takeoff quantity.")
            continue
        try:
            quantity = _convert(units, raw_quantity, product.unit_code)
        except UnitValidationError as exc:
            warnings.append(f"{obj.name}: BOM quantity rejected — {exc}")
            continue
        group = bom_groups.setdefault(product.id, {"quantity": Decimal(0), "sources": []})
        group["quantity"] += quantity.value
        group["sources"].append(obj.id)

        mapping_id = getattr(obj, "position_mapping_id", None)
        if mapping_id is None:
            warnings.append(f"{obj.name}: no BOQ position mapping assigned; omitted from BOQ.")
            continue
        mapping = mappings.get(mapping_id)
        if mapping is None or not mapping.enabled:
            warnings.append(f"{obj.name}: BOQ mapping is missing or disabled; omitted from BOQ.")
            continue
        if mapping.product_reference_id != product.id:
            warnings.append(f"{obj.name}: BOQ mapping product does not match the assigned product.")
            continue
        position = positions.get(mapping.position_reference_id)
        if position is None:
            warnings.append(f"{obj.name}: mapped BOQ position is missing.")
            continue

        rule = mapping.measurement_rule_code.upper()
        if rule in {"LENGTH", "LINEAR_CENTERLINE_LENGTH"} and isinstance(obj, LinearElement):
            boq_quantity = obj.length
        elif rule == "COUNT":
            boq_quantity = Quantity(value=Decimal(1), unit_code="piece")
        else:
            warnings.append(
                f"{obj.name}: measurement rule '{mapping.measurement_rule_code}' "
                "is not supported for this object type; omitted from BOQ."
            )
            continue
        try:
            measured = _convert(units, boq_quantity, position.unit_code)
        except UnitValidationError as exc:
            warnings.append(f"{obj.name}: BOQ quantity rejected — {exc}")
            continue
        group = boq_groups.setdefault(
            mapping.id,
            {"mapping": mapping, "position": position, "quantity": Decimal(0), "sources": []},
        )
        group["quantity"] += measured.value
        group["sources"].append(obj.id)

    bom_items = tuple(
        BOMItem(
            product_reference_id=product_id,
            quantity=Quantity(
                value=data["quantity"],
                unit_code=products[product_id].unit_code,
            ),
            source_object_ids=tuple(data["sources"]),
        )
        for product_id, data in sorted(bom_groups.items(), key=lambda item: products[item[0]].product_code)
    )
    boq_items = tuple(
        BOQItem(
            position_reference_id=data["position"].id,
            quantity=Quantity(
                value=data["quantity"],
                unit_code=data["position"].unit_code,
            ),
            source_object_ids=tuple(data["sources"]),
            mapping_id=data["mapping"].id,
            measurement_rule_code=data["mapping"].measurement_rule_code,
            measurement_rule_version=data["mapping"].mapping_version,
        )
        for _, data in sorted(boq_groups.items(), key=lambda item: (
            item[1]["position"].position_code, item[1]["mapping"].mapping_code
        ))
    )

    bom = BOMDocument(
        project_id=model.project.id,
        title=f"{title} — BOM",
        items=bom_items,
    )
    boq = BOQDocument(
        project_id=model.project.id,
        title=f"{title} — BOQ",
        items=boq_items,
    )
    updated = model.model_copy(update={
        "bom_documents": (*model.bom_documents, bom),
        "boq_documents": (*model.boq_documents, boq),
    })
    ModelValidator(unit_service=units).validate(updated).raise_for_errors()
    return TakeoffResult(model=updated, bom=bom, boq=boq, warnings=tuple(warnings))
