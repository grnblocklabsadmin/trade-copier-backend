"""add run_id to execution_logs

Revision ID: b21153173943
Revises: 4aed72fd6c0c
Create Date: 2026-03-15 10:33:12.033237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b21153173943"
down_revision: Union[str, Sequence[str], None] = "4aed72fd6c0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "execution_logs",
        sa.Column("run_id", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("execution_logs", "run_id")