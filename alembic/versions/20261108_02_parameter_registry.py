"""Add the versioned engineering parameter registry.

Revision ID: 20261108_02
Revises: ad37aa2b962f
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261108_02"
down_revision: str | Sequence[str] | None = "ad37aa2b962f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parameter_definitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("discipline_code", sa.String(length=80), nullable=False),
        sa.Column("category_code", sa.String(length=80), nullable=False),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_parameter_definitions_code"),
    )
    op.create_table(
        "parameter_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("definition_id", sa.String(length=36), nullable=False),
        sa.Column("revision_code", sa.String(length=80), nullable=False),
        sa.Column("scope_kind", sa.String(length=24), nullable=False),
        sa.Column("scope_key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["definition_id"],
            ["parameter_definitions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "definition_id",
            "scope_kind",
            "scope_key",
            "revision_code",
            name="uq_parameter_revision_scope_code",
        ),
    )
    op.create_index(
        "ix_parameter_revision_resolution",
        "parameter_revisions",
        ["definition_id", "scope_kind", "scope_key", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_parameter_revision_resolution", table_name="parameter_revisions")
    op.drop_table("parameter_revisions")
    op.drop_table("parameter_definitions")
