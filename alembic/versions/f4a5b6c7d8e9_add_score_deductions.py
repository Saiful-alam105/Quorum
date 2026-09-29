"""add score deductions to analysis_runs

Revision ID: f4a5b6c7d8e9
Revises: f3a4b5c6d7e8
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op

revision = "f4a5b6c7d8e9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analysis_runs",
        sa.Column("security_deduction", sa.Integer(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("test_deduction", sa.Integer(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("coverage_deduction", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("analysis_runs", "coverage_deduction")
    op.drop_column("analysis_runs", "test_deduction")
    op.drop_column("analysis_runs", "security_deduction")