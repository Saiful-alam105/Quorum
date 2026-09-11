"""add user_id to repositories

Revision ID: d2b3c4d5e6f7
Revises: c1a2b3d4e5f6
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Associate repositories with the Quorum user that owns them."""
    op.add_column("repositories", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_repositories_user_id"), "repositories", ["user_id"], unique=False
    )
    op.create_foreign_key(
        "fk_repositories_user_id", "repositories", "users", ["user_id"], ["id"]
    )


def downgrade() -> None:
    """Remove the user association from repositories."""
    op.drop_constraint("fk_repositories_user_id", "repositories", type_="foreignkey")
    op.drop_index(op.f("ix_repositories_user_id"), table_name="repositories")
    op.drop_column("repositories", "user_id")