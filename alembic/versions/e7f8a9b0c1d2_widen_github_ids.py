"""widen github id columns to BIGINT

Revision ID: e7f8a9b0c1d2
Revises: d2b3c4d5e6f7
Create Date: 2026-09-13 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """GitHub resource IDs exceed 32-bit range; widen them to BIGINT."""
    op.alter_column("users", "github_id", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column(
        "users",
        "github_installation_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
    )
    op.alter_column(
        "repositories", "github_id", existing_type=sa.Integer(), type_=sa.BigInteger()
    )
    op.alter_column(
        "pull_requests", "github_id", existing_type=sa.Integer(), type_=sa.BigInteger()
    )


def downgrade() -> None:
    """Restore 32-bit integer GitHub IDs."""
    op.alter_column("pull_requests", "github_id", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column(
        "repositories", "github_id", existing_type=sa.BigInteger(), type_=sa.Integer()
    )
    op.alter_column(
        "users",
        "github_installation_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
    )
    op.alter_column("users", "github_id", existing_type=sa.BigInteger(), type_=sa.Integer())