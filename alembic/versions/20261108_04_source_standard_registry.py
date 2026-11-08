"""Add global source and standard-reference registry.

Revision ID: 20261108_04
Revises: 20261108_03
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261108_04"
down_revision: str | Sequence[str] | None = "20261108_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_references",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_kind", sa.String(length=40), nullable=False),
        sa.Column("document_name", sa.String(length=240), nullable=True),
        sa.Column("document_revision", sa.String(length=120), nullable=True),
        sa.Column("uri", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_source_references_identity",
        "source_references",
        ["source_kind", "document_name", "document_revision"],
    )
    op.create_index(
        "ix_source_references_hash",
        "source_references",
        ["content_hash"],
    )
    op.create_table(
        "standard_references",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("standard_code", sa.String(length=120), nullable=False),
        sa.Column("edition", sa.String(length=80), nullable=False),
        sa.Column("jurisdiction", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("clause", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("source_reference_id", sa.String(length=36), nullable=True),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_reference_id"], ["source_references.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "standard_code",
            "edition",
            "jurisdiction",
            "clause",
            name="uq_standard_reference_edition_clause",
        ),
    )
    op.create_index(
        "ix_standard_references_code_edition",
        "standard_references",
        ["standard_code", "edition"],
    )


def downgrade() -> None:
    op.drop_index("ix_standard_references_code_edition", table_name="standard_references")
    op.drop_table("standard_references")
    op.drop_index("ix_source_references_hash", table_name="source_references")
    op.drop_index("ix_source_references_identity", table_name="source_references")
    op.drop_table("source_references")
