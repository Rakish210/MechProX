from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mechprox.data.db import Base


class ProjectSnapshotRecord(Base):
    """Persisted, versioned JSON snapshot of a single engineering project."""

    __tablename__ = "project_snapshots"
    __table_args__ = (UniqueConstraint("project_code", name="uq_project_snapshots_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ParameterDefinitionRecord(Base):
    """Queryable index plus canonical typed JSON for a parameter definition."""

    __tablename__ = "parameter_definitions"
    __table_args__ = (UniqueConstraint("code", name="uq_parameter_definitions_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    discipline_code: Mapped[str] = mapped_column(String(80), nullable=False)
    category_code: Mapped[str] = mapped_column(String(80), nullable=False)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ParameterRevisionRecord(Base):
    """Immutable parameter revision with indexed scope and effective dates."""

    __tablename__ = "parameter_revisions"
    __table_args__ = (
        UniqueConstraint(
            "definition_id",
            "scope_kind",
            "scope_key",
            "revision_code",
            name="uq_parameter_revision_scope_code",
        ),
        Index(
            "ix_parameter_revision_resolution",
            "definition_id",
            "scope_kind",
            "scope_key",
            "status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("parameter_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_code: Mapped[str] = mapped_column(String(80), nullable=False)
    scope_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductCatalogRecord(Base):
    """Global catalogue index and canonical typed product record."""

    __tablename__ = "catalogue_products"
    __table_args__ = (
        UniqueConstraint(
            "catalogue_code", "product_code", name="uq_catalogue_product_code"
        ),
        Index("ix_catalogue_products_category", "category_code", "name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    catalogue_code: Mapped[str] = mapped_column(String(120), nullable=False)
    product_code: Mapped[str] = mapped_column(String(120), nullable=False)
    category_code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PositionCatalogRecord(Base):
    """Global BOQ/public-works position catalogue index."""

    __tablename__ = "catalogue_positions"
    __table_args__ = (
        UniqueConstraint(
            "catalogue_code", "position_code", name="uq_catalogue_position_code"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    catalogue_code: Mapped[str] = mapped_column(String(120), nullable=False)
    position_code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(40), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PositionProductMappingRecord(Base):
    """Persistent, versioned many-to-many mapping between BOQ positions and products."""

    __tablename__ = "catalogue_position_product_mappings"
    __table_args__ = (
        UniqueConstraint(
            "mapping_code", "mapping_version", name="uq_catalogue_mapping_version"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    position_reference_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("catalogue_positions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_reference_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("catalogue_products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    mapping_code: Mapped[str] = mapped_column(String(120), nullable=False)
    mapping_version: Mapped[str] = mapped_column(String(80), nullable=False)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceReferenceRecord(Base):
    """Queryable index for an immutable source-document reference."""

    __tablename__ = "source_references"
    __table_args__ = (
        Index(
            "ix_source_references_identity",
            "source_kind",
            "document_name",
            "document_revision",
        ),
        Index("ix_source_references_hash", "content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    document_name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    document_revision: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StandardReferenceRecord(Base):
    """Indexed standard edition/clause linked to its source document."""

    __tablename__ = "standard_references"
    __table_args__ = (
        UniqueConstraint(
            "standard_code",
            "edition",
            "jurisdiction",
            "clause",
            name="uq_standard_reference_edition_clause",
        ),
        Index("ix_standard_references_code_edition", "standard_code", "edition"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    standard_code: Mapped[str] = mapped_column(String(120), nullable=False)
    edition: Mapped[str] = mapped_column(String(80), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    clause: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_reference_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("source_references.id", ondelete="RESTRICT"),
        nullable=True,
    )
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
