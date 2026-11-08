"""Add persistent product, position and mapping catalogues.

Revision ID: 20261108_03
Revises: 20261108_02
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261108_03"
down_revision: str | Sequence[str] | None = "20261108_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalogue_products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("catalogue_code", sa.String(length=120), nullable=False),
        sa.Column("product_code", sa.String(length=120), nullable=False),
        sa.Column("category_code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "catalogue_code", "product_code", name="uq_catalogue_product_code"
        ),
    )
    op.create_index(
        "ix_catalogue_products_category",
        "catalogue_products",
        ["category_code", "name"],
    )
    op.create_table(
        "catalogue_positions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("catalogue_code", sa.String(length=120), nullable=False),
        sa.Column("position_code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("unit_code", sa.String(length=40), nullable=False),
        sa.Column("jurisdiction", sa.String(length=80), nullable=True),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "catalogue_code", "position_code", name="uq_catalogue_position_code"
        ),
    )
    op.create_table(
        "catalogue_position_product_mappings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("position_reference_id", sa.String(length=36), nullable=False),
        sa.Column("product_reference_id", sa.String(length=36), nullable=False),
        sa.Column("mapping_code", sa.String(length=120), nullable=False),
        sa.Column("mapping_version", sa.String(length=80), nullable=False),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["position_reference_id"], ["catalogue_positions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["product_reference_id"], ["catalogue_products.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "mapping_code", "mapping_version", name="uq_catalogue_mapping_version"
        ),
    )


def downgrade() -> None:
    op.drop_table("catalogue_position_product_mappings")
    op.drop_table("catalogue_positions")
    op.drop_index("ix_catalogue_products_category", table_name="catalogue_products")
    op.drop_table("catalogue_products")
