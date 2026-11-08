from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from mechprox.data.models import (
    PositionCatalogRecord,
    PositionProductMappingRecord,
    ProductCatalogRecord,
)
from mechprox.domain.commercial import (
    PositionProductMapping,
    PositionReference,
    ProductReference,
)


class CatalogueConflictError(ValueError):
    """Raised when a catalogue code or mapping version is already registered."""


@dataclass(frozen=True, slots=True)
class CatalogueSnapshot:
    products: tuple[ProductReference, ...]
    positions: tuple[PositionReference, ...]
    mappings: tuple[PositionProductMapping, ...]


class CatalogueRepository:
    """Persistent, typed product/position catalogue independent of project snapshots."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def register_product(self, product: ProductReference) -> ProductReference:
        record = ProductCatalogRecord(
            id=str(product.id),
            catalogue_code=product.catalogue_code,
            product_code=product.product_code,
            category_code=product.category_code,
            name=product.name,
            model_json=product.model_dump_json(),
            created_at=datetime.now(UTC),
        )
        try:
            with self._session_factory.begin() as session:
                session.add(record)
                session.flush()
        except IntegrityError as exc:
            raise CatalogueConflictError(
                f"Product '{product.catalogue_code}/{product.product_code}' already exists."
            ) from exc
        return product

    def register_position(self, position: PositionReference) -> PositionReference:
        record = PositionCatalogRecord(
            id=str(position.id),
            catalogue_code=position.catalogue_code,
            position_code=position.position_code,
            name=position.name,
            unit_code=position.unit_code,
            jurisdiction=position.jurisdiction,
            model_json=position.model_dump_json(),
            created_at=datetime.now(UTC),
        )
        try:
            with self._session_factory.begin() as session:
                session.add(record)
                session.flush()
        except IntegrityError as exc:
            raise CatalogueConflictError(
                f"Position '{position.catalogue_code}/{position.position_code}' already exists."
            ) from exc
        return position

    def register_mapping(self, mapping: PositionProductMapping) -> PositionProductMapping:
        try:
            with self._session_factory.begin() as session:
                if session.get(PositionCatalogRecord, str(mapping.position_reference_id)) is None:
                    raise ValueError("Mapping references an unknown catalogue position.")
                if session.get(ProductCatalogRecord, str(mapping.product_reference_id)) is None:
                    raise ValueError("Mapping references an unknown catalogue product.")
                session.add(
                    PositionProductMappingRecord(
                        id=str(mapping.id),
                        position_reference_id=str(mapping.position_reference_id),
                        product_reference_id=str(mapping.product_reference_id),
                        mapping_code=mapping.mapping_code,
                        mapping_version=mapping.mapping_version,
                        model_json=mapping.model_dump_json(),
                        created_at=datetime.now(UTC),
                    )
                )
                session.flush()
        except IntegrityError as exc:
            raise CatalogueConflictError(
                f"Mapping '{mapping.mapping_code}/{mapping.mapping_version}' already exists."
            ) from exc
        return mapping

    def export_snapshot(self) -> CatalogueSnapshot:
        with self._session_factory() as session:
            products = session.scalars(
                select(ProductCatalogRecord).order_by(
                    ProductCatalogRecord.category_code,
                    ProductCatalogRecord.name,
                )
            ).all()
            positions = session.scalars(
                select(PositionCatalogRecord).order_by(
                    PositionCatalogRecord.catalogue_code,
                    PositionCatalogRecord.position_code,
                )
            ).all()
            mappings = session.scalars(
                select(PositionProductMappingRecord).order_by(
                    PositionProductMappingRecord.mapping_code,
                    PositionProductMappingRecord.mapping_version,
                )
            ).all()
        return CatalogueSnapshot(
            products=tuple(ProductReference.model_validate_json(row.model_json) for row in products),
            positions=tuple(PositionReference.model_validate_json(row.model_json) for row in positions),
            mappings=tuple(
                PositionProductMapping.model_validate_json(row.model_json) for row in mappings
            ),
        )

    def get_product(self, product_id: UUID) -> ProductReference:
        with self._session_factory() as session:
            record = session.get(ProductCatalogRecord, str(product_id))
            if record is None:
                raise LookupError(f"Product '{product_id}' was not found.")
            payload = record.model_json
        return ProductReference.model_validate_json(payload)

    def get_position(self, position_id: UUID) -> PositionReference:
        with self._session_factory() as session:
            record = session.get(PositionCatalogRecord, str(position_id))
            if record is None:
                raise LookupError(f"Position '{position_id}' was not found.")
            payload = record.model_json
        return PositionReference.model_validate_json(payload)
