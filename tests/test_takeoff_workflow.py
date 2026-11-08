from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.data import models  # noqa: F401
from mechprox.data.db import Base
from mechprox.data.project_repository import CommercialAppendError, ProjectRepository
from mechprox.domain.commercial import PositionProductMapping, PositionReference, ProductReference
from mechprox.domain.enums import InformationOrigin
from mechprox.domain.model import EngineeringModel
from mechprox.domain.project import Project
from mechprox.workflows.engineering_objects import add_linear_element
from mechprox.workflows.takeoff import generate_takeoff


@pytest.fixture
def repository(tmp_path: Path) -> ProjectRepository:
    engine = create_engine(f"sqlite:///{tmp_path / 'takeoff.db'}")
    Base.metadata.create_all(engine)
    return ProjectRepository(sessionmaker(bind=engine, expire_on_commit=False))


def _catalogue_records():
    product = ProductReference(
        catalogue_code="USER",
        product_code="PIPE-25",
        name="Steel pipe DN25",
        category_code="25.3",
        unit_code="meter",
        origin=InformationOrigin.USER_INPUT,
    )
    position = PositionReference(
        catalogue_code="USER-BOQ",
        position_code="25.300.001",
        name="Steel pipe installation",
        unit_code="meter",
        unit_price=Decimal("125.50"),
        currency_code="TRY",
    )
    mapping = PositionProductMapping(
        position_reference_id=position.id,
        product_reference_id=product.id,
        mapping_code="PIPE-LENGTH",
        mapping_version="1",
        measurement_rule_code="LINEAR_CENTERLINE_LENGTH",
    )
    return product, position, mapping


def _model_with_two_pipes():
    model = EngineeringModel(project=Project(project_code="TO-001", name="Takeoff test"))
    product, position, mapping = _catalogue_records()
    model = add_linear_element(
        model, name="Pipe A", category_code="pipe", discipline_code="PLUMBING",
        element_type="pipe", length_value=Decimal("3.5"), length_unit="meter",
        product=product, mapping=mapping, position=position, changed_by="test",
    )
    model = add_linear_element(
        model, name="Pipe B", category_code="pipe", discipline_code="PLUMBING",
        element_type="pipe", length_value=Decimal("250"), length_unit="centimeter",
        product=product, mapping=mapping, position=position, changed_by="test",
    )
    return model


def test_takeoff_aggregates_lengths_and_preserves_sources() -> None:
    model = _model_with_two_pipes()

    result = generate_takeoff(model, title="Test")

    assert len(result.bom.items) == 1
    assert result.bom.items[0].quantity.value == Decimal("6.0")
    assert result.bom.items[0].source_object_ids == tuple(item.id for item in model.objects)
    assert len(result.boq.items) == 1
    assert result.boq.items[0].quantity.value == Decimal("6.0")
    assert result.boq.items[0].measurement_rule_version == "1"
    assert result.warnings == ()


def test_takeoff_rejects_unmapped_position_without_inventing_boq() -> None:
    model = _model_with_two_pipes()
    objects = tuple(item.model_copy(update={"position_mapping_id": None}) for item in model.objects)
    model = model.model_copy(update={"objects": objects})

    result = generate_takeoff(model)

    assert len(result.bom.items) == 1
    assert result.boq.items == ()
    assert len(result.warnings) == 2


def test_takeoff_documents_are_appended_atomically(repository: ProjectRepository) -> None:
    model = _model_with_two_pipes()
    repository.create(model)
    result = generate_takeoff(model)

    repository.append_commercial_documents(model, result.bom, result.boq)
    restored = repository.get(model.project.id)

    assert restored.bom_documents == (result.bom,)
    assert restored.boq_documents == (result.boq,)


def test_takeoff_append_rejects_stale_project_snapshot(repository: ProjectRepository) -> None:
    model = _model_with_two_pipes()
    repository.create(model)
    result = generate_takeoff(model)
    changed = model.model_copy(
        update={"project": model.project.model_copy(update={"name": "Changed"})}
    )
    repository.save(changed)

    with pytest.raises(CommercialAppendError, match="project changed"):
        repository.append_commercial_documents(model, result.bom, result.boq)
