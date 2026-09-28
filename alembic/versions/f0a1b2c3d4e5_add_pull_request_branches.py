"""add pull request branch references

Revision ID: f0a1b2c3d4e5
Revises: a1b2c3d4e5f8
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from alembic import op

revision = "f0a1b2c3d4e5"
down_revision = "a1b2c3d4e5f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pull_requests",
        sa.Column("head_ref", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column("base_ref", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pull_requests", "base_ref")
    op.drop_column("pull_requests", "head_ref")