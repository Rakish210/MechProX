from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.data import models  # noqa: F401
from mechprox.data.catalogue_repository import CatalogueConflictError, CatalogueRepository
from mechprox.data.db import Base
from mechprox.domain.commercial import PositionProductMapping, PositionReference, ProductReference
from mechprox.domain.enums import InformationOrigin


@pytest.fixture
def repository(tmp_path: Path) -> CatalogueRepository:
    engine = create_engine(f"sqlite:///{tmp_path / 'catalogue.db'}")
    Base.metadata.create_all(engine)
    return CatalogueRepository(sessionmaker(bind=engine, expire_on_commit=False))


def _product() -> ProductReference:
    return ProductReference(
        catalogue_code="USER",
        product_code="PIPE-STEEL-DN25",
        name="Çelik boru DN25",
        category_code="25.3",
        unit_code="meter",
        origin=InformationOrigin.USER_INPUT,
    )


def _position() -> PositionReference:
    return PositionReference(
        catalogue_code="USER-BOQ",
        position_code="25.300.001",
        name="Çelik boru döşenmesi",
        unit_code="meter",
        jurisdiction="TR",
    )


def test_catalogue_round_trip_and_mapping(repository: CatalogueRepository) -> None:
    product = _product()
    position = _position()
    repository.register_product(product)
    repository.register_position(position)
    mapping = PositionProductMapping(
        position_reference_id=position.id,
        product_reference_id=product.id,
        mapping_code="PIPE-INSTALL",
        mapping_version="1",
        measurement_rule_code="LENGTH",
    )
    repository.register_mapping(mapping)

    snapshot = repository.export_snapshot()

    assert snapshot.products == (product,)
    assert snapshot.positions == (position,)
    assert snapshot.mappings == (mapping,)


def test_duplicate_product_code_is_rejected(repository: CatalogueRepository) -> None:
    product = _product()
    repository.register_product(product)

    with pytest.raises(CatalogueConflictError):
        repository.register_product(product.model_copy(update={"id": product.id.__class__()}))


def test_mapping_requires_registered_product_and_position(
    repository: CatalogueRepository,
) -> None:
    product = _product()
    position = _position()
    mapping = PositionProductMapping(
        position_reference_id=position.id,
        product_reference_id=product.id,
        mapping_code="MISSING",
        mapping_version="1",
        measurement_rule_code="COUNT",
    )

    with pytest.raises(ValueError, match="unknown catalogue position"):
        repository.register_mapping(mapping)
