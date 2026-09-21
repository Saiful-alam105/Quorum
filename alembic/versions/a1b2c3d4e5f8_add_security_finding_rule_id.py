"""add rule_id to security_findings

Revision ID: a1b2c3d4e5f8
Revises: e7f8a9b0c1d2
Create Date: 2026-09-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f8"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store the Semgrep rule id with each security finding (Phase 8)."""
    op.add_column(
        "security_findings",
        sa.Column("rule_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Drop the rule_id column."""
    op.drop_column("security_findings", "rule_id")