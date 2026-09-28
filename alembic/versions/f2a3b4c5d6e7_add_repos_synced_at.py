"""add repos_synced_at to users

Revision ID: f2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op

revision = "f2a3b4c5d6e7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("repos_synced_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "repos_synced_at")