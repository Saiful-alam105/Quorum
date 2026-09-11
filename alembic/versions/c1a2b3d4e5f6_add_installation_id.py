"""add github_installation_id to users

Revision ID: c1a2b3d4e5f6
Revises: 303b9ed314cd
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "303b9ed314cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add github_installation_id column to users."""
    op.add_column("users", sa.Column("github_installation_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Drop github_installation_id column from users."""
    op.drop_column("users", "github_installation_id")