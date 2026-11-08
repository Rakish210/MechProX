"""Initial MechPro project snapshot storage.

Revision ID: ad37aa2b962f
Revises:
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ad37aa2b962f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("model_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_code", name="uq_project_snapshots_code"),
    )


def downgrade() -> None:
    op.drop_table("project_snapshots")
