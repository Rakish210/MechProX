from decimal import Decimal
from uuid import uuid4

from mechprox.domain.base import Quantity, Revision
from mechprox.domain.commercial import PositionProductMapping, PositionReference, ProductReference
from mechprox.domain.engineering import Equipment, LinearElement
from mechprox.domain.enums import InformationOrigin, RevisionState
from mechprox.domain.model import EngineeringModel
from mechprox.domain.project import Discipline
from mechprox.domain.validation import ModelValidator


class EngineeringObjectInputError(ValueError):
    """Raised when an engineering object cannot be added safely."""


def _merge_catalogue_records(model: EngineeringModel, product: ProductReference,
                             mapping: PositionProductMapping | None,
                             position: PositionReference | None) -> dict:
    products = {item.id: item for item in model.products}
    existing_product = products.get(product.id)
    if existing_product is not None and existing_product != product:
        raise EngineeringObjectInputError("Product ID conflicts with a different project record.")
    products[product.id] = product

    positions = {item.id: item for item in model.positions}
    mappings = {item.id: item for item in model.position_product_mappings}
    if mapping is not None:
        if position is None or mapping.product_reference_id != product.id:
            raise EngineeringObjectInputError("A mapping must reference the selected product and its position.")
        existing_position = positions.get(position.id)
        if existing_position is not None and existing_position != position:
            raise EngineeringObjectInputError("Position ID conflicts with a different project record.")
        existing_mapping = mappings.get(mapping.id)
        if existing_mapping is not None and existing_mapping != mapping:
            raise EngineeringObjectInputError("Mapping ID conflicts with a different project record.")
        positions[position.id] = position
        mappings[mapping.id] = mapping
    return {
        "products": tuple(products.values()),
        "positions": tuple(positions.values()),
        "position_product_mappings": tuple(mappings.values()),
    }


def _discipline_records(model: EngineeringModel, code: str) -> tuple[Discipline, ...]:
    matches = [item for item in model.disciplines if item.code == code]
    if len(matches) > 1:
        raise EngineeringObjectInputError(f"Project contains duplicate discipline '{code}'.")
    return model.disciplines if matches else (*model.disciplines, Discipline(code=code, name=code))


def add_linear_element(
    model: EngineeringModel,
    *,
    name: str,
    category_code: str,
    discipline_code: str,
    element_type: str,
    length_value: Decimal,
    length_unit: str,
    product: ProductReference,
    mapping: PositionProductMapping | None = None,
    position: PositionReference | None = None,
    changed_by: str,
) -> EngineeringModel:
    normalized = (name.strip(), category_code.strip(), discipline_code.strip(),
                  element_type.strip(), changed_by.strip(), length_unit.strip())
    if not all(normalized):
        raise EngineeringObjectInputError("Name, category, discipline, element type, unit and creator are required.")
    if not length_value.is_finite() or length_value <= 0:
        raise EngineeringObjectInputError("Linear-element length must be finite and greater than zero.")
    if not product.unit_code:
        raise EngineeringObjectInputError("The selected product has no unit.")
    object_id = uuid4()
    revision = Revision(
        object_id=object_id,
        revision_code="A",
        state=RevisionState.DRAFT,
        changed_by=changed_by.strip(),
        change_summary="Initial linear engineering object created in MechProX.",
    )
    obj = LinearElement(
        id=object_id,
        project_id=model.project.id,
        name=name.strip(),
        category_code=category_code.strip(),
        discipline_code=discipline_code.strip().upper(),
        element_type=element_type.strip(),
        length=Quantity(value=length_value, unit_code=length_unit.strip()),
        material_product_reference_id=product.id,
        position_mapping_id=mapping.id if mapping else None,
        information_origin=InformationOrigin.USER_INPUT,
        revision_id=revision.id,
    )
    updated = model.model_copy(update={
        **_merge_catalogue_records(model, product, mapping, position),
        "disciplines": _discipline_records(model, discipline_code.strip().upper()),
        "revisions": (*model.revisions, revision),
        "objects": (*model.objects, obj),
    })
    ModelValidator().validate(updated).raise_for_errors()
    return updated


def add_equipment(
    model: EngineeringModel,
    *,
    name: str,
    category_code: str,
    discipline_code: str,
    equipment_type: str,
    product: ProductReference,
    mapping: PositionProductMapping | None = None,
    position: PositionReference | None = None,
    changed_by: str,
) -> EngineeringModel:
    normalized = (name.strip(), category_code.strip(), discipline_code.strip(),
                  equipment_type.strip(), changed_by.strip())
    if not all(normalized):
        raise EngineeringObjectInputError("Name, category, discipline, equipment type and creator are required.")
    object_id = uuid4()
    revision = Revision(
        object_id=object_id,
        revision_code="A",
        state=RevisionState.DRAFT,
        changed_by=changed_by.strip(),
        change_summary="Initial equipment object created in MechProX.",
    )
    obj = Equipment(
        id=object_id,
        project_id=model.project.id,
        name=name.strip(),
        category_code=category_code.strip(),
        discipline_code=discipline_code.strip().upper(),
        equipment_type=equipment_type.strip(),
        product_reference_id=product.id,
        position_mapping_id=mapping.id if mapping else None,
        information_origin=InformationOrigin.USER_INPUT,
        revision_id=revision.id,
    )
    updated = model.model_copy(update={
        **_merge_catalogue_records(model, product, mapping, position),
        "disciplines": _discipline_records(model, discipline_code.strip().upper()),
        "revisions": (*model.revisions, revision),
        "objects": (*model.objects, obj),
    })
    ModelValidator().validate(updated).raise_for_errors()
    return updated
